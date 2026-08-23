"""Panda design-import adapter with durable non-idempotency fencing."""

from __future__ import annotations

import io
import hashlib
import json
import mimetypes
import os
import re
import stat
import urllib.error
import urllib.parse
import urllib.request
import uuid
import zipfile
from dataclasses import dataclass
from pathlib import Path
from pathlib import PurePosixPath
from typing import Any, Callable, Dict, Mapping, Optional, Sequence, Tuple

from .artifacts import (
    MAX_ENTRIES,
    MAX_EXPANDED_BYTES,
    MAX_FILE_BYTES,
    MAX_PACKET_BYTES,
    assert_publishable_content,
)
from .errors import AmbiguousPublishError, ContractError, PublishError, ReceiptError
from .models import PublicationOutcome, PublicationReceipt, require_sha256
from .store import InventorStore

DEFAULT_API = "https://panda-social-api.autonomous.ai/api/v1"
HTTP_TIMEOUT_SECONDS = 120
Transport = Callable[[str, str, Mapping[str, str], Optional[bytes], int], "HttpResponse"]

# Only response classes that prove the server rejected the request before
# applying it may reopen a non-idempotent effect.  Redirects, timeouts,
# conflicts, throttling, and unexpected success statuses remain ambiguous.
PROVEN_NO_EFFECT_STATUSES = frozenset(
    (400, 401, 403, 404, 405, 406, 410, 411, 412, 413, 414, 415, 416, 417, 421, 422, 426, 428, 431, 451)
)
IMPORT_STRING_LIMITS = {
    "title": 300,
    "description": 20_000,
    "category": 100,
    "prompt": 50_000,
    "license": 100,
}
CORE_IMPORT_FIELDS = frozenset(
    ("_core_artifact_sha256", "_core_owner_id", "_core_api_origin")
)
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
_OPEN_SUPPORTS_DIR_FD = os.open in getattr(os, "supports_dir_fd", set())


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Authenticated API calls never forward a bearer through a redirect."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        return None


@dataclass(frozen=True)
class HttpResponse:
    status: int
    headers: Mapping[str, str]
    body: bytes

    def __post_init__(self) -> None:
        if (
            not isinstance(self.status, int)
            or isinstance(self.status, bool)
            or not 100 <= self.status <= 599
        ):
            raise ContractError("HTTP response status must be an integer from 100 to 599")
        if not isinstance(self.headers, Mapping):
            raise ContractError("HTTP response headers must be a mapping")
        if not isinstance(self.body, bytes):
            raise ContractError("HTTP response body must be bytes")
        if len(self.body) > MAX_RESPONSE_BYTES:
            raise PublishError("Panda response exceeds the 2 MB safety limit")


def urllib_transport(
    method: str,
    url: str,
    headers: Mapping[str, str],
    body: Optional[bytes],
    timeout: int,
) -> HttpResponse:
    request = urllib.request.Request(url, method=method, data=body)
    for name, value in headers.items():
        request.add_header(name, value)
    try:
        opener = urllib.request.build_opener(_NoRedirectHandler())
        with opener.open(request, timeout=timeout) as response:
            content = response.read(MAX_RESPONSE_BYTES + 1)
            if len(content) > MAX_RESPONSE_BYTES:
                raise PublishError("Panda response exceeds the 2 MB safety limit")
            return HttpResponse(response.status, dict(response.headers), content)
    except urllib.error.HTTPError as exc:
        content = exc.read(MAX_RESPONSE_BYTES + 1)
        if len(content) > MAX_RESPONSE_BYTES:
            raise PublishError("Panda error response exceeds the 2 MB safety limit")
        return HttpResponse(exc.code, dict(exc.headers or {}), content)


def _json_body(response: HttpResponse) -> Mapping[str, Any]:
    def reject_duplicate_keys(pairs):  # type: ignore[no-untyped-def]
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError("duplicate JSON key %r" % key)
            value[key] = item
        return value

    try:
        value = json.loads(
            response.body.decode("utf-8"), object_pairs_hook=reject_duplicate_keys
        )
    except (UnicodeDecodeError, ValueError) as exc:
        raise PublishError("Panda returned invalid JSON (HTTP %s): %s" % (response.status, exc))
    if not isinstance(value, Mapping):
        raise PublishError("Panda returned a non-object JSON response")
    return value


def _normalize_import_metadata(
    metadata: Mapping[str, Any], *, allow_core_fields: bool = False
) -> Dict[str, Any]:
    if not isinstance(metadata, Mapping):
        raise ContractError("Panda import metadata must be an object")
    if not all(isinstance(name, str) for name in metadata):
        raise ContractError("Panda import metadata field names must be strings")
    allowed = set(IMPORT_STRING_LIMITS) | {"tags", "status"}
    if allow_core_fields:
        allowed |= set(CORE_IMPORT_FIELDS)
    unknown = set(metadata) - allowed
    if unknown:
        raise ContractError("unknown Panda import metadata fields: %s" % sorted(unknown))
    normalized: Dict[str, Any] = {"status": metadata.get("status", "draft")}
    if normalized["status"] != "draft":
        raise ContractError("core import always requires status=draft")
    for name, limit in IMPORT_STRING_LIMITS.items():
        value = metadata.get(name)
        if value is None:
            continue
        if not isinstance(value, str) or not value.strip() or len(value) > limit:
            raise ContractError(
                "Panda %s must be a non-empty string of at most %d characters"
                % (name, limit)
            )
        normalized[name] = value
    if "title" not in normalized:
        raise ContractError("Panda import title is required")
    tags = metadata.get("tags") or []
    if (
        not isinstance(tags, list)
        or len(tags) > 50
        or any(
            not isinstance(tag, str) or not tag.strip() or len(tag) > 100
            for tag in tags
        )
        or len(tags) != len(set(tags))
    ):
        raise ContractError("Panda tags must be at most 50 unique non-empty strings")
    normalized["tags"] = list(tags)
    assert_publishable_content(
        "publication-metadata.json",
        json.dumps(
            normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8"),
    )
    return normalized


def _origin(url: str) -> str:
    try:
        parsed = urllib.parse.urlsplit(url)
        port = parsed.port
    except (TypeError, ValueError) as exc:
        raise ContractError("Panda API base is malformed") from exc
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise ContractError("Panda API base must be an HTTPS origin/path without credentials or query")
    return "https://%s%s" % (parsed.hostname.lower(), ":%d" % port if port else "")


def _safe_zip_path(value: str) -> str:
    candidate = PurePosixPath(value)
    if (
        not value
        or not candidate.parts
        or value in (".", "..")
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
        or "\\" in value
        or candidate.is_absolute()
        or ".." in candidate.parts
        or candidate.as_posix() != value
    ):
        raise ContractError("publish packet contains an unsafe member path")
    return value


def _validate_upload_filename(filename: str) -> str:
    if (
        not isinstance(filename, str)
        or not filename
        or len(filename) > 255
        or PurePosixPath(filename).name != filename
        or any(ord(character) < 32 or ord(character) == 127 for character in filename)
    ):
        raise ContractError("Panda upload filename must be one safe basename")
    assert_publishable_content(filename, b"")
    return filename


def _read_packet_bytes(packet: Path) -> bytes:
    """Read one regular file while refusing replaced/symlinked path components."""
    # O_NONBLOCK prevents a regular-file-to-FIFO race from hanging before the
    # descriptor can be inspected and rejected.
    flags = (
        os.O_RDONLY
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    directory_flags = flags | getattr(os, "O_DIRECTORY", 0)
    descriptor = None
    directory_descriptor = None
    try:
        expected_file = packet.lstat()
        expected_parent = packet.parent.stat()
    except (OSError, ValueError) as exc:
        raise ContractError(
            "cannot inspect publish packet %s: %s" % (packet, exc)
        ) from exc
    if not stat.S_ISREG(expected_file.st_mode):
        raise ContractError(
            "publish packet must be a regular non-symlink file: %s" % packet
        )
    try:
        if _OPEN_SUPPORTS_DIR_FD and hasattr(os, "O_DIRECTORY"):
            # Resolve an intentionally supplied parent alias once, then walk
            # the canonical path through descriptors. If any canonical parent
            # is swapped for a symlink between resolution and open, O_NOFOLLOW
            # rejects it instead of redirecting the bearer-bound upload.
            parent = packet.parent.resolve(strict=True)
            anchor = Path(parent.anchor)
            directory_descriptor = os.open(str(anchor), directory_flags)
            for part in parent.parts[1:]:
                child = os.open(part, directory_flags, dir_fd=directory_descriptor)
                os.close(directory_descriptor)
                directory_descriptor = child
            opened_parent = os.fstat(directory_descriptor)
            if (opened_parent.st_dev, opened_parent.st_ino) != (
                expected_parent.st_dev,
                expected_parent.st_ino,
            ):
                raise ContractError(
                    "publish packet parent was replaced while opening: %s"
                    % packet.parent
                )
            descriptor = os.open(packet.name, flags, dir_fd=directory_descriptor)
            opened_file = os.fstat(descriptor)
            if (opened_file.st_dev, opened_file.st_ino) != (
                expected_file.st_dev,
                expected_file.st_ino,
            ):
                raise ContractError(
                    "publish packet was replaced while opening: %s" % packet
                )
        else:
            parent = packet.parent.resolve(strict=True)
            resolved_parent = parent.stat()
            if (resolved_parent.st_dev, resolved_parent.st_ino) != (
                expected_parent.st_dev,
                expected_parent.st_ino,
            ):
                raise ContractError(
                    "publish packet parent was replaced while opening: %s"
                    % packet.parent
                )
            descriptor = os.open(str(parent / packet.name), flags)
            opened = os.fstat(descriptor)
            if (opened.st_dev, opened.st_ino) != (
                expected_file.st_dev,
                expected_file.st_ino,
            ):
                raise ContractError(
                    "publish packet was replaced while opening: %s" % packet
                )
    except ContractError:
        if descriptor is not None:
            os.close(descriptor)
            descriptor = None
        raise
    except (OSError, ValueError) as exc:
        if descriptor is not None:
            os.close(descriptor)
            descriptor = None
        raise ContractError(
            "cannot safely open publish packet %s: %s" % (packet, exc)
        ) from exc
    finally:
        if directory_descriptor is not None:
            os.close(directory_descriptor)
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise ContractError(
                "publish packet must be a regular non-symlink file: %s" % packet
            )
        chunks = []
        total = 0
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > MAX_PACKET_BYTES:
                raise ContractError("publish packet exceeds the 50 MB client limit")
        after = os.fstat(descriptor)
        if after.st_size != opened.st_size or after.st_mtime_ns != opened.st_mtime_ns:
            raise ContractError("publish packet changed while it was read: %s" % packet)
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _validate_packet_bytes(content: bytes) -> Tuple[bytes, str, str]:
    """Verify immutable bytes as one exact canonical core publish packet."""
    if type(content) is not bytes:
        raise ContractError("publish packet content must be immutable bytes")
    if len(content) > MAX_PACKET_BYTES:
        raise ContractError("publish packet exceeds the 50 MB client limit")
    packet_sha256 = hashlib.sha256(content).hexdigest()
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            infos = archive.infolist()
            names = [info.filename for info in infos]
            if archive.comment:
                raise ContractError("publish packet must not contain a zip comment")
            if len(infos) > MAX_ENTRIES + 1 or len(names) != len(set(names)):
                raise ContractError("publish packet has too many or duplicate members")
            for name in names:
                _safe_zip_path(name)
            if names.count("_inventor-artifact.json") != 1:
                raise ContractError("publish packet needs exactly one core artifact manifest")
            if any(info.is_dir() for info in infos):
                raise ContractError("publish packet must contain files, not directory members")
            if any(
                info.compress_type != zipfile.ZIP_STORED
                or info.date_time != (1980, 1, 1, 0, 0, 0)
                or info.create_system != 3
                or info.extra
                or info.comment
                or info.flag_bits & 0x1
                for info in infos
            ):
                raise ContractError("publish packet members are not in canonical core form")
            if any(info.file_size > MAX_FILE_BYTES for info in infos):
                raise ContractError("publish packet contains an oversized expanded file")
            if sum(info.file_size for info in infos) > MAX_EXPANDED_BYTES:
                raise ContractError("publish packet exceeds the expanded-size limit")
            raw_manifest = json.loads(archive.read("_inventor-artifact.json").decode("utf-8"))
            if (
                not isinstance(raw_manifest, Mapping)
                or set(raw_manifest) != {
                    "schema_version",
                    "artifact_sha256",
                    "total_bytes",
                    "created_at",
                    "entries",
                }
                or type(raw_manifest.get("schema_version")) is not int
                or raw_manifest.get("schema_version") != 1
                or raw_manifest.get("created_at") != "content-addressed"
            ):
                raise ContractError("publish packet artifact manifest is malformed")
            raw_entries = raw_manifest.get("entries")
            if not isinstance(raw_entries, list) or not raw_entries:
                raise ContractError("publish packet artifact manifest has no entries")
            canonical_entries = []
            expected_names = []
            verified_members = {}
            total_bytes = 0
            info_by_name = {info.filename: info for info in infos}
            for raw in raw_entries:
                if not isinstance(raw, Mapping) or set(raw) != {
                    "path", "bytes", "sha256", "executable"
                }:
                    raise ContractError("publish packet artifact entry is malformed")
                name = _safe_zip_path(raw.get("path")) if isinstance(raw.get("path"), str) else ""
                size = raw.get("bytes")
                digest = raw.get("sha256")
                executable = raw.get("executable")
                if (
                    not name
                    or name == "_inventor-artifact.json"
                    or not isinstance(size, int)
                    or isinstance(size, bool)
                    or size < 0
                    or not isinstance(executable, bool)
                ):
                    raise ContractError("publish packet artifact entry has invalid fields")
                require_sha256(digest, "publish packet entry sha256")
                if name in expected_names or name not in info_by_name:
                    raise ContractError("publish packet manifest inventory does not match the zip")
                member = archive.read(name)
                assert_publishable_content(name, member)
                if len(member) != size or hashlib.sha256(member).hexdigest() != digest:
                    raise ContractError("publish packet member does not match its manifest")
                mode = (info_by_name[name].external_attr >> 16) & 0o777
                if mode != (0o755 if executable else 0o644):
                    raise ContractError("publish packet permissions do not match its manifest")
                canonical_entries.append(
                    {"path": name, "bytes": size, "sha256": digest, "executable": executable}
                )
                verified_members[name] = member
                expected_names.append(name)
                total_bytes += size
            if expected_names != sorted(expected_names):
                raise ContractError("publish packet manifest entries must be sorted")
            if set(names) != set(expected_names) | {"_inventor-artifact.json"}:
                raise ContractError("publish packet has undeclared members")
            if (
                type(raw_manifest.get("total_bytes")) is not int
                or raw_manifest.get("total_bytes") != total_bytes
            ):
                raise ContractError("publish packet manifest total_bytes is inconsistent")
            artifact_sha256 = hashlib.sha256(
                json.dumps(
                    canonical_entries,
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=False,
                ).encode("utf-8")
            ).hexdigest()
            if raw_manifest.get("artifact_sha256") != artifact_sha256:
                raise ContractError("publish packet artifact identity is inconsistent")
            canonical_buffer = io.BytesIO()
            with zipfile.ZipFile(
                canonical_buffer, "w", compression=zipfile.ZIP_STORED
            ) as canonical_archive:
                for entry in canonical_entries:
                    name = entry["path"]
                    info = zipfile.ZipInfo(
                        name, date_time=(1980, 1, 1, 0, 0, 0)
                    )
                    info.compress_type = zipfile.ZIP_STORED
                    info.create_system = 3
                    info.external_attr = (
                        (0o755 if entry["executable"] else 0o644) & 0xFFFF
                    ) << 16
                    canonical_archive.writestr(
                        info,
                        verified_members[name],
                        compress_type=zipfile.ZIP_STORED,
                    )
                info = zipfile.ZipInfo(
                    "_inventor-artifact.json",
                    date_time=(1980, 1, 1, 0, 0, 0),
                )
                info.compress_type = zipfile.ZIP_STORED
                info.create_system = 3
                info.external_attr = (0o644 & 0xFFFF) << 16
                canonical_archive.writestr(
                    info,
                    json.dumps(
                        raw_manifest,
                        sort_keys=True,
                        separators=(",", ":"),
                        ensure_ascii=False,
                    ).encode("utf-8")
                    + b"\n",
                    compress_type=zipfile.ZIP_STORED,
                )
            if canonical_buffer.getvalue() != content:
                raise ContractError(
                    "publish packet bytes are not the exact canonical core ZIP"
                )
    except (OSError, UnicodeDecodeError, ValueError, zipfile.BadZipFile) as exc:
        raise ContractError("publish packet is not a valid core zip: %s" % exc) from exc
    return content, packet_sha256, artifact_sha256


def _load_packet(packet: Path) -> Tuple[bytes, str, str]:
    """Read once, verify the core manifest, and identify the exact upload bytes."""
    return _validate_packet_bytes(_read_packet_bytes(Path(packet)))


def inspect_publish_packet(packet: Path) -> Dict[str, Any]:
    """Validate a canonical packet and return its content identity.

    This intentionally exposes identities and counts, not the packet bytes.
    Uploads remain responsible for reading and validating the exact bytes at
    the effect boundary through :class:`PandaClient`.
    """
    content, packet_sha256, artifact_sha256 = _load_packet(Path(packet))
    with zipfile.ZipFile(io.BytesIO(content), "r") as archive:
        entries = len(archive.infolist())
    return {
        "bytes": len(content),
        "entries": entries,
        "packet_sha256": packet_sha256,
        "artifact_sha256": artifact_sha256,
    }


def _multipart(
    fields: Sequence[Tuple[str, str]], files: Sequence[Tuple[str, str, str, bytes]]
) -> Tuple[bytes, str]:
    boundary = "inventor-core-%s" % uuid.uuid4().hex
    buffer = io.BytesIO()
    marker = ("--%s\r\n" % boundary).encode("ascii")
    for name, value in fields:
        buffer.write(marker)
        buffer.write(
            ('Content-Disposition: form-data; name="%s"\r\n\r\n' % name).encode("utf-8")
        )
        buffer.write(value.encode("utf-8"))
        buffer.write(b"\r\n")
    for name, filename, content_type, content in files:
        safe_name = re.sub(r"[^A-Za-z0-9_.-]", "_", filename)
        buffer.write(marker)
        buffer.write(
            (
                'Content-Disposition: form-data; name="%s"; filename="%s"\r\n'
                % (name, safe_name)
            ).encode("utf-8")
        )
        buffer.write(("Content-Type: %s\r\n\r\n" % content_type).encode("ascii"))
        buffer.write(content)
        buffer.write(b"\r\n")
    buffer.write(("--%s--\r\n" % boundary).encode("ascii"))
    return buffer.getvalue(), "multipart/form-data; boundary=%s" % boundary


class PandaClient:
    def __init__(
        self,
        token: str,
        api_base: str = DEFAULT_API,
        transport: Transport = urllib_transport,
        timeout_seconds: int = HTTP_TIMEOUT_SECONDS,
        allowed_origins: Optional[Sequence[str]] = None,
    ) -> None:
        if not isinstance(token, str) or not token or "\r" in token or "\n" in token:
            raise ContractError("Panda bearer token is required")
        origin = _origin(api_base)
        if isinstance(allowed_origins, (str, bytes)):
            raise ContractError("Panda allowed_origins must be a sequence of HTTPS origins")
        allowed = {_origin(item) for item in (allowed_origins or (DEFAULT_API,))}
        if origin not in allowed:
            raise ContractError(
                "Panda API origin %s is not pinned in allowed_origins" % origin
            )
        self._token = token
        self.api_base = api_base.rstrip("/")
        self.api_origin = origin
        self.transport = transport
        if (
            not isinstance(timeout_seconds, int)
            or isinstance(timeout_seconds, bool)
            or timeout_seconds <= 0
        ):
            raise ContractError("Panda timeout_seconds must be a positive integer")
        self.timeout_seconds = timeout_seconds

    def _request(
        self,
        method: str,
        path: str,
        body: Optional[bytes] = None,
        content_type: Optional[str] = None,
    ) -> HttpResponse:
        headers = {"Authorization": "Bearer %s" % self._token, "Accept": "application/json"}
        if content_type:
            headers["Content-Type"] = content_type
        return self.transport(
            method,
            self.api_base + path,
            headers,
            body,
            self.timeout_seconds,
        )

    def import_design(self, packet: Path, metadata: Mapping[str, Any]) -> HttpResponse:
        packet = Path(packet)
        content = _load_packet(packet)[0]
        return self.import_design_bytes(packet.name, content, metadata)

    def import_design_bytes(
        self, filename: str, content: bytes, metadata: Mapping[str, Any]
    ) -> HttpResponse:
        filename = _validate_upload_filename(filename)
        content = _validate_packet_bytes(content)[0]
        metadata = _normalize_import_metadata(metadata, allow_core_fields=True)
        fields = [("status", "draft")]
        for name in ("title", "description", "category", "prompt", "license"):
            if metadata.get(name) is not None:
                fields.append((name, str(metadata[name])))
        tags = metadata["tags"]
        for tag in tags:
            fields.append(("tags", str(tag)))
        content_type = mimetypes.guess_type(filename)[0] or "application/zip"
        body, multipart_type = _multipart(
            fields, (("file", filename, content_type, content),)
        )
        return self._request("POST", "/designs/import", body, multipart_type)

    def get_design(self, slug: str) -> HttpResponse:
        return self._request("GET", "/designs/%s" % urllib.parse.quote(slug, safe=""))

    def publish(self, slug: str, price_cents: int) -> HttpResponse:
        if (
            not isinstance(price_cents, int)
            or isinstance(price_cents, bool)
            or not 100 <= price_cents <= 1_000_000
        ):
            raise ContractError("price_cents must be an integer in Panda's 100..1000000 range")
        body = json.dumps({"listing": {"price_cents": price_cents}}).encode("utf-8")
        return self._request(
            "POST", "/designs/%s/publish" % urllib.parse.quote(slug, safe=""), body, "application/json"
        )

    def unpublish(self, slug: str) -> HttpResponse:
        return self._request(
            "POST",
            "/designs/%s/unpublish" % urllib.parse.quote(slug, safe=""),
            b"{}",
            "application/json",
        )


class PandaPublicationCoordinator:
    """Outbox coordinator; every remote effect is recorded before sending."""

    def __init__(self, store: InventorStore, client: PandaClient, owner_id: str) -> None:
        if not isinstance(owner_id, str) or not owner_id:
            raise ContractError("inventor Panda owner_id is required")
        self.store = store
        self.client = client
        self.owner_id = owner_id

    def import_draft(
        self,
        product_id: str,
        packet: Path,
        metadata: Mapping[str, Any],
        lease_token: Optional[str] = None,
    ) -> PublicationOutcome:
        packet = Path(packet)
        metadata = _normalize_import_metadata(metadata)
        packet_bytes, packet_sha, artifact_sha = _load_packet(packet)
        _validate_upload_filename(packet.name)
        product = self.store.get_product(product_id)
        if not product.get("artifact_sha256"):
            raise ContractError("product must bind exact artifact bytes before publication")
        if product["artifact_sha256"] != artifact_sha:
            raise ContractError(
                "publish packet artifact does not match the product's selected artifact"
            )
        request = dict(metadata)
        request["_core_artifact_sha256"] = artifact_sha
        request["_core_owner_id"] = self.owner_id
        request["_core_api_origin"] = self.client.api_origin
        intent = self.store.prepare_publish(
            product_id,
            packet_sha,
            request,
            remote_slug_hint=None,
            lease_token=lease_token,
        )
        if intent["state"] in ("succeeded", "live"):
            receipt = PublicationReceipt(**intent["receipt"])
            receipt.assert_owner(self.owner_id)
            receipt.assert_artifact(artifact_sha)
            return PublicationOutcome(intent["id"], receipt)
        intent = self.store.begin_publish(intent["id"], lease_token=lease_token)
        effect_token = intent["effect_token"]
        try:
            response = self.client.import_design_bytes(
                packet.name, packet_bytes, intent["request"]
            )
        except Exception as exc:
            self.store.mark_publish_unknown(
                intent["id"], effect_token, "%s: %s" % (type(exc).__name__, exc)
            )
            raise AmbiguousPublishError(
                "Panda import outcome is unknown; intent %s must be reconciled before retry"
                % intent["id"]
            ) from exc
        if response.status != 201:
            summary = response.body.decode("utf-8", "replace")[:500]
            if response.status in PROVEN_NO_EFFECT_STATUSES:
                self.store.mark_publish_rejected(
                    intent["id"],
                    effect_token,
                    "HTTP %s: %s" % (response.status, summary),
                )
                raise PublishError(
                    "Panda rejected import (HTTP %s): %s" % (response.status, summary)
                )
            self.store.mark_publish_unknown(
                intent["id"],
                effect_token,
                "HTTP %s: %s" % (response.status, summary),
            )
            raise AmbiguousPublishError(
                "Panda import returned HTTP %s; reconcile intent %s before retry"
                % (response.status, intent["id"])
            )
        try:
            design = _json_body(response)
            receipt = PublicationReceipt.from_design(design, packet_sha, artifact_sha)
            receipt.assert_owner(self.owner_id)
            if receipt.status != "draft":
                raise ReceiptError("Panda import did not return the required draft state")
            self.store.mark_publish_succeeded(
                intent["id"], effect_token, receipt, response=design
            )
            return PublicationOutcome(intent["id"], receipt)
        except Exception as exc:
            try:
                current = self.store.get_publish_intent(intent["id"])
                if current["state"] == "sending":
                    self.store.mark_publish_unknown(
                        intent["id"],
                        effect_token,
                        "201 response did not produce a valid draft receipt",
                    )
            except Exception:
                pass
            raise AmbiguousPublishError(
                "Panda accepted import but no valid receipt was recorded; reconcile intent %s"
                % intent["id"]
            ) from exc

    def reconcile_import(self, intent_id: str, remote_slug: str) -> PublicationReceipt:
        """Fail closed until Panda exposes a remote content/idempotency identity."""
        del remote_slug
        intent = self.store.get_publish_intent(intent_id)
        if intent["state"] != "unknown":
            raise PublishError("intent %s is not awaiting import reconciliation" % intent_id)
        raise AmbiguousPublishError(
            "Panda readback does not expose a packet/tree hash, so a slug cannot prove "
            "which bytes created intent %s; backend idempotency support is required"
            % intent_id
        )

    def publish_live(
        self, intent_id: str, price_cents: int, lease_token: Optional[str] = None
    ) -> PublicationReceipt:
        if (
            not isinstance(price_cents, int)
            or isinstance(price_cents, bool)
            or not 100 <= price_cents <= 1_000_000
        ):
            raise ContractError("price_cents must be an integer in Panda's 100..1000000 range")
        intent = self.store.get_publish_intent(intent_id)
        if intent["state"] == "live":
            return PublicationReceipt(**intent["receipt"])
        if intent["state"] != "succeeded":
            raise AmbiguousPublishError(
                "intent %s is %s, not a proven draft" % (intent_id, intent["state"])
            )
        draft = PublicationReceipt(**intent["receipt"])
        draft.assert_owner(self.owner_id)
        # Persist an intermediate state before the second non-idempotent-facing effect.
        live_request = {
            "api_origin": self.client.api_origin,
            "owner_id": self.owner_id,
            "listing": {"price_cents": price_cents},
        }
        intent = self.store.begin_live(intent_id, live_request, lease_token=lease_token)
        effect_token = intent["effect_token"]
        try:
            persisted_price = intent["live_request"]["listing"]["price_cents"]
            response = self.client.publish(draft.slug, persisted_price)
        except Exception as exc:
            self.store.mark_live_unknown(
                intent_id, effect_token, "%s: %s" % (type(exc).__name__, exc)
            )
            raise AmbiguousPublishError(
                "publish outcome is unknown; reconcile intent %s before retry" % intent_id
            ) from exc
        if response.status not in (200, 201):
            summary = response.body.decode("utf-8", "replace")[:500]
            if response.status in PROVEN_NO_EFFECT_STATUSES:
                self.store.restore_draft_after_publish_rejection(
                    intent_id,
                    effect_token,
                    "HTTP %s: %s" % (response.status, summary),
                )
                raise PublishError(
                    "Panda rejected publish (HTTP %s): %s" % (response.status, summary)
                )
            self.store.mark_live_unknown(
                intent_id, effect_token, "HTTP %s: %s" % (response.status, summary)
            )
            raise AmbiguousPublishError(
                "publish outcome is unknown; reconcile intent %s" % intent_id
            )
        return self._readback_live(intent_id, draft, effect_token=effect_token)

    def reconcile_live(self, intent_id: str) -> PublicationReceipt:
        intent = self.store.get_publish_intent(intent_id)
        if intent["state"] != "live_unknown":
            raise PublishError("intent %s is not awaiting live reconciliation" % intent_id)
        draft = PublicationReceipt(**intent["receipt"])
        return self._readback_live(intent_id, draft, reconciling=True)

    def _readback_live(
        self,
        intent_id: str,
        draft: PublicationReceipt,
        reconciling: bool = False,
        effect_token: Optional[str] = None,
    ) -> PublicationReceipt:
        try:
            response = self.client.get_design(draft.slug)
        except Exception as exc:
            if not reconciling:
                self.store.mark_live_unknown(
                    intent_id, effect_token, "readback failed: %s" % exc
                )
            raise AmbiguousPublishError("public readback failed for intent %s" % intent_id) from exc
        if response.status != 200:
            if not reconciling:
                self.store.mark_live_unknown(
                    intent_id, effect_token, "readback HTTP %s" % response.status
                )
            raise AmbiguousPublishError("public readback returned HTTP %s" % response.status)
        try:
            receipt = PublicationReceipt.from_design(
                _json_body(response), draft.packet_sha256, draft.artifact_sha256
            )
            receipt.assert_owner(self.owner_id)
            intent = self.store.get_publish_intent(intent_id)
            live_request = intent.get("live_request")
            if not isinstance(live_request, Mapping):
                raise ReceiptError("publish intent lacks its persisted live request")
            listing_request = live_request.get("listing")
            if not isinstance(listing_request, Mapping):
                raise ReceiptError("publish intent has a malformed listing request")
            receipt.assert_listing(listing_request.get("price_cents"))
            if (
                receipt.design_id != draft.design_id
                or receipt.root_id != draft.root_id
                or receipt.slug != draft.slug
                or receipt.current_history_id != draft.current_history_id
                or receipt.project_url != draft.project_url
            ):
                raise ReceiptError("public readback does not identify the exact draft history")
        except Exception as exc:
            if not reconciling:
                try:
                    current = self.store.get_publish_intent(intent_id)
                    if current["state"] == "publishing":
                        self.store.mark_live_unknown(
                            intent_id,
                            effect_token,
                            "public readback was malformed or identified different bytes",
                        )
                except Exception:
                    pass
            raise AmbiguousPublishError(
                "public readback did not produce a trustworthy receipt for intent %s"
                % intent_id
            ) from exc
        if not receipt.is_verified_public:
            if not reconciling:
                self.store.mark_live_unknown(
                    intent_id,
                    effect_token,
                    "readback did not prove current version public",
                )
            raise AmbiguousPublishError(
                "one draft readback cannot prove a publish effect failed; intent remains unknown"
            )
        if reconciling:
            self.store.resolve_live_as_public(intent_id, receipt)
        else:
            self.store.mark_publish_live(intent_id, effect_token, receipt)
        return receipt
