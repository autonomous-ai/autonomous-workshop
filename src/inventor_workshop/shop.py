"""Authenticated Shop Door transport and durable Shop send fencing."""

from __future__ import annotations

import io
import hashlib
import json
import mimetypes
import re
import tempfile
import urllib.parse
import uuid
import zipfile
from pathlib import Path
from pathlib import PurePosixPath
from typing import Any, Callable, Dict, Mapping, Optional, Sequence, Tuple

from .artifacts import (
    ArtifactManifest,
    assert_packable_content,
    build_artifact_manifest,
    build_pack,
)
from .attribution import attribute_product_description
from ._http import Transport, _NoRedirectHandler, make_urllib_transport
from ._http import HttpResponse as _HttpResponse
from .pack import _load_pack, _validate_pack_bytes
from .errors import (
    AmbiguousPublishError,
    ContractError,
    PublishError,
    ReceiptError,
    StateConflict,
)
from .models import PublicationOutcome, PublicationReceipt, require_sha256
from .store import InventorStore

DEFAULT_SHOP_API = "https://panda-social-api.autonomous.ai/api/v1"
DEFAULT_SHOP_PAGE_BASE = "https://www.autonomous.ai/factory/product"
SHOP_USER_AGENT = "Mozilla/5.0 (compatible; AutonomousWorkshop/1.0)"
HTTP_TIMEOUT_SECONDS = 120

# Only response classes that prove the server rejected the request before
# applying it may reopen a non-idempotent effect.  Redirects, timeouts,
# conflicts, throttling, and unexpected success statuses remain ambiguous.
PROVEN_NO_EFFECT_STATUSES = frozenset(
    (400, 401, 403, 404, 405, 406, 410, 411, 412, 413, 414, 415, 416, 417, 421, 422, 426, 428, 431, 451)
)
SHOP_LISTING_STRING_LIMITS = {
    "title": 300,
    "description": 2_000,
    "category": 100,
    "prompt": 50_000,
    "license": 60,
}
WORKSHOP_SHOP_LISTING_FIELDS = frozenset(
    (
        "_workshop_artifact_sha256",
        "_workshop_cover_bytes",
        "_workshop_cover_content_type",
        "_workshop_cover_filename",
        "_workshop_cover_sha256",
        "_workshop_instructions_sha256",
        "_workshop_playtest_evidence_sha256",
        "_workshop_owner_id",
        "_workshop_api_origin",
    )
)
LEGACY_SHOP_LISTING_FIELDS = frozenset(
    (
        "_foundation_artifact_sha256",
        "_foundation_owner_id",
        "_foundation_api_origin",
        "_core_artifact_sha256",
        "_core_owner_id",
        "_core_api_origin",
    )
)
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
MAX_UPLOAD_BYTES = 50 * 1024 * 1024
SHOP_INSTRUCTIONS_IMAGES = ("hero", "play", "detail", "parts", "box")
SHOP_CATEGORY_BY_LANE = {
    "classics-made-yours": "toys",
    "invented-games": "toys",
    "moving-machines": "toys",
    "holdable-science": "toys",
    "little-worlds": "toys",
}
SHOP_CONTENT_IMAGE_URL_LIMIT = 2_048
SHOP_CONTENT_VIDEO_SUFFIXES = (".mp4", ".webm", ".mov", ".m4v", ".avi")
SHOP_IMPORT_THUMBNAIL_MAX_BYTES = 5 * 1024 * 1024
SHOP_IMPORT_THUMBNAIL_TYPES = frozenset(("image/jpeg", "image/png", "image/webp"))


def _canonical_sha256(value: Any) -> str:
    try:
        payload = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ContractError("Shop request must contain finite JSON values") from exc
    return hashlib.sha256(payload).hexdigest()


def _assert_shop_importable_pack(content: bytes) -> None:
    """Mirror the Shop's shallow design discovery before bearer-bound HTTP.

    Workshop Packs contain the Made artifact at archive root.  The deployed
    importer recognizes that root only when it has a usable ``project.json`` or
    a top-level Python source containing ``def gen_step``.  Checking the exact
    sealed Pack prevents an avoidable rejected import and, critically, never
    patches un-Playtested bytes into the archive after Make.
    """

    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            names = set(archive.namelist())
            top_level_generator = False
            for name in sorted(names):
                if not name.casefold().endswith(".py"):
                    continue
                if b"def gen_step" not in archive.read(name):
                    continue
                if "/" in name:
                    raise ContractError(
                        "Shop import would narrow this artifact to nested generator %s"
                        % name
                    )
                top_level_generator = True
            if "project.json" in names:
                try:
                    project = json.loads(
                        archive.read("project.json").decode("utf-8")
                    )
                except (UnicodeDecodeError, ValueError):
                    project = None
                if isinstance(project, Mapping):
                    return
            if top_level_generator:
                return
    except (KeyError, OSError, UnicodeDecodeError, ValueError, zipfile.BadZipFile) as exc:
        raise ContractError("Shop importability check could not read the sealed Pack") from exc
    raise ContractError(
        "Shop import requires a valid root project.json or a top-level *.py "
        "defining gen_step in the sealed Made artifact"
    )


def _normalize_import_thumbnail(value: Optional[Mapping[str, Any]]) -> Optional[Dict[str, Any]]:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise ContractError("Shop import thumbnail must be an object")
    filename = _validate_upload_filename(value.get("filename"))
    content = value.get("content")
    content_type = value.get("content_type")
    if (
        type(content) is not bytes
        or not content
        or len(content) > SHOP_IMPORT_THUMBNAIL_MAX_BYTES
    ):
        raise ContractError("Shop import thumbnail must be 1 byte..5 MB")
    if content_type not in SHOP_IMPORT_THUMBNAIL_TYPES:
        raise ContractError("Shop import thumbnail must be PNG, JPEG, or WebP")
    digest = hashlib.sha256(content).hexdigest()
    expected_digest = value.get("sha256")
    if expected_digest is not None and expected_digest != digest:
        raise ContractError("Shop import thumbnail sha256 does not match its bytes")
    return {
        "filename": filename,
        "content": content,
        "content_type": content_type,
        "sha256": digest,
    }


def _https_url(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 4096:
        raise ContractError("%s must be an absolute HTTPS URL" % label)
    try:
        parsed = urllib.parse.urlsplit(value)
    except ValueError as exc:
        raise ContractError("%s must be an absolute HTTPS URL" % label) from exc
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise ContractError("%s must be an absolute HTTPS URL" % label)
    return value


def _shop_product_page_url(slug: Any) -> str:
    """Return the customer page, never the immutable project CDN directory."""

    if not isinstance(slug, str) or not slug or len(slug) > 300:
        raise ReceiptError("Shop product page requires a canonical slug")
    return _https_url(
        DEFAULT_SHOP_PAGE_BASE + "/" + urllib.parse.quote(slug, safe=""),
        "Shop product page URL",
    )


def _shop_category_for_lane(lane: Any) -> str:
    """Translate Workshop lanes into the Shop's stable public taxonomy."""

    if not isinstance(lane, str) or lane not in SHOP_CATEGORY_BY_LANE:
        raise ContractError("product page lane has no Shop category mapping")
    return SHOP_CATEGORY_BY_LANE[lane]


def _shop_content_image_url(value: Any, label: str) -> str:
    """Apply the stricter URL contract used by Shop product-page images."""

    url = _https_url(value, label)
    if len(url) > SHOP_CONTENT_IMAGE_URL_LIMIT:
        raise ContractError(
            "%s must be at most %d characters" % (label, SHOP_CONTENT_IMAGE_URL_LIMIT)
        )
    path = urllib.parse.urlsplit(url).path.casefold()
    if any(path.endswith(suffix) for suffix in SHOP_CONTENT_VIDEO_SUFFIXES):
        raise ContractError("%s must identify a static image" % label)
    return url


def _plain_text(value: Any, label: str, minimum: int, maximum: int) -> str:
    if (
        not isinstance(value, str)
        or value != value.strip()
        or not minimum <= len(value) <= maximum
        or "<" in value
        or ">" in value
        or any(
            ord(character) < 32 and character not in "\n\r\t"
            or ord(character) == 127
            for character in value
        )
    ):
        raise ContractError(
            "%s must be %d..%d characters of plain text" % (label, minimum, maximum)
        )
    return value


def _normalize_attachments(value: Sequence[Mapping[str, Any]]) -> list:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ContractError("Shop attachments must be a sequence")
    if len(value) > 12:
        raise ContractError("Shop accepts at most 12 attachments")
    normalized = []
    for index, item in enumerate(value):
        if (
            not isinstance(item, Mapping)
            or set(item) != {"kind", "url"}
            or item.get("kind") not in ("image", "video")
        ):
            raise ContractError("Shop attachment %d is malformed" % index)
        normalized.append(
            {
                "kind": item["kind"],
                "url": _https_url(item.get("url"), "Shop attachment URL"),
            }
        )
    return normalized


def _normalize_use_case(value: Mapping[str, Any]) -> Dict[str, str]:
    if not isinstance(value, Mapping) or set(value) != {"label", "body", "image"}:
        raise ContractError("Shop use_case must contain label, body, and image")
    return {
        "label": _plain_text(value.get("label"), "use_case.label", 1, 40),
        "body": _plain_text(value.get("body"), "use_case.body", 180, 400),
        "image": _shop_content_image_url(value.get("image"), "use_case.image"),
    }


def _normalize_story_blocks(value: Sequence[Mapping[str, Any]]) -> list:
    if (
        isinstance(value, (str, bytes))
        or not isinstance(value, Sequence)
        or len(value) > 10
    ):
        raise ContractError("Shop story_blocks must contain at most 10 blocks")
    normalized = []
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            raise ContractError("story_blocks[%d] must be an object" % index)
        unknown = set(item) - {"lead", "body", "hero_image", "pair_images"}
        if unknown or not {"lead", "body"} <= set(item):
            raise ContractError("story_blocks[%d] is malformed" % index)
        block: Dict[str, Any] = {
            "lead": _plain_text(
                item.get("lead"), "story_blocks[%d].lead" % index, 1, 40
            ),
            "body": _plain_text(
                item.get("body"), "story_blocks[%d].body" % index, 180, 400
            ),
        }
        hero = item.get("hero_image")
        if hero:
            block["hero_image"] = _shop_content_image_url(
                hero, "story_blocks[%d].hero_image" % index
            )
        pairs = item.get("pair_images", [])
        if (
            isinstance(pairs, (str, bytes))
            or not isinstance(pairs, Sequence)
            or len(pairs) > 10
        ):
            raise ContractError(
                "story_blocks[%d].pair_images must contain at most 10 URLs" % index
            )
        normalized_pairs = [
            _shop_content_image_url(url, "story_blocks[%d].pair_images" % index)
            for url in pairs
        ]
        # The Shop's Go response uses ``omitempty`` for this optional gallery.
        # Omitting an empty list here makes the sent value, persisted proof, and
        # authenticated readback share one canonical representation.
        if normalized_pairs:
            block["pair_images"] = normalized_pairs
        normalized.append(block)
    return normalized


def _design_with_normalized_currency(design: Mapping[str, Any]) -> Mapping[str, Any]:
    """Accept the deployed API's lowercase ``usd`` without weakening currency proof."""

    copied = dict(design)
    listing = copied.get("listing")
    if isinstance(listing, Mapping):
        normalized_listing = dict(listing)
        currency = normalized_listing.get("currency")
        if isinstance(currency, str) and currency.casefold() == "usd":
            normalized_listing["currency"] = "USD"
        copied["listing"] = normalized_listing
    return copied


def _receipt_with_details(
    receipt: PublicationReceipt, details: Mapping[str, Any]
) -> PublicationReceipt:
    value = receipt.to_dict()
    merged = dict(value.get("details") or {})
    merged.update(dict(details))
    value["details"] = merged
    return PublicationReceipt.from_dict(value)


class HttpResponse(_HttpResponse):
    """Shop Door's bounded response.

    A body over ``MAX_RESPONSE_BYTES`` fails at construction time, not only
    when read off the wire, so a caller who builds one from local bytes (see
    ``ShopInstructionsWriter._read_page``) gets the same guarantee the
    transport already gives every network response.
    """

    def __post_init__(self) -> None:
        super().__post_init__()
        if len(self.body) > MAX_RESPONSE_BYTES:
            raise PublishError("Shop response exceeds the 2 MB safety limit")


urllib_transport = make_urllib_transport(MAX_RESPONSE_BYTES, oversize_error=PublishError)


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
        raise PublishError(
            "Shop Door returned invalid JSON (HTTP %s): %s"
            % (response.status, exc)
        )
    if not isinstance(value, Mapping):
        raise PublishError("Shop Door returned a non-object JSON response")
    return value


def _normalize_shop_listing(
    metadata: Mapping[str, Any],
    *,
    allow_workshop_fields: bool = False,
    inventor_name: Optional[str] = None,
) -> Dict[str, Any]:
    if not isinstance(metadata, Mapping):
        raise ContractError("Shop listing must be an object")
    if not all(isinstance(name, str) for name in metadata):
        raise ContractError("Shop listing field names must be strings")
    allowed = set(SHOP_LISTING_STRING_LIMITS) | {"tags", "status"}
    if allow_workshop_fields:
        allowed |= set(WORKSHOP_SHOP_LISTING_FIELDS)
        allowed |= set(LEGACY_SHOP_LISTING_FIELDS)
    unknown = set(metadata) - allowed
    if unknown:
        raise ContractError("unknown Shop listing fields: %s" % sorted(unknown))
    normalized: Dict[str, Any] = {"status": metadata.get("status", "draft")}
    if normalized["status"] != "draft":
        raise ContractError("Workshop import always requires status=draft")
    for name, limit in SHOP_LISTING_STRING_LIMITS.items():
        value = metadata.get(name)
        if value is None:
            continue
        if name == "description" and inventor_name is not None:
            value = attribute_product_description(value, inventor_name)
        if (
            not isinstance(value, str)
            or value != value.strip()
            or not value
            or len(value) > limit
        ):
            raise ContractError(
                "Shop listing %s must be a trimmed non-empty string of at most %d characters"
                % (name, limit)
            )
        normalized[name] = value
    if "title" not in normalized:
        raise ContractError("Shop listing title is required")
    tags = metadata.get("tags")
    if tags is None:
        tags = []
    if (
        not isinstance(tags, list)
        or len(tags) > 10
        or any(
            not isinstance(tag, str)
            or tag != tag.strip()
            or not tag
            or len(tag) > 40
            for tag in tags
        )
        or len(tags) != len({tag.casefold() for tag in tags})
    ):
        raise ContractError(
            "Shop listing tags must be at most 10 case-insensitively unique "
            "trimmed strings of at most 40 characters"
        )
    normalized["tags"] = list(tags)
    assert_packable_content(
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
        raise ContractError("Shop Door API base is malformed") from exc
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise ContractError(
            "Shop Door API base must be an HTTPS origin/path without credentials or query"
        )
    return "https://%s%s" % (parsed.hostname.lower(), ":%d" % port if port else "")


def _validate_upload_filename(filename: str) -> str:
    if (
        not isinstance(filename, str)
        or not filename
        or len(filename) > 255
        or PurePosixPath(filename).name != filename
        or any(ord(character) < 32 or ord(character) == 127 for character in filename)
    ):
        raise ContractError("Shop upload filename must be one safe basename")
    assert_packable_content(filename, b"")
    return filename


def _multipart(
    fields: Sequence[Tuple[str, str]], files: Sequence[Tuple[str, str, str, bytes]]
) -> Tuple[bytes, str]:
    boundary = "inventor-workshop-%s" % uuid.uuid4().hex
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


class ShopDoor:
    """Authenticated Door into the optional product Shop."""

    name = "shop"

    def __init__(
        self,
        token: str,
        api_base: str = DEFAULT_SHOP_API,
        transport: Transport = urllib_transport,
        timeout_seconds: int = HTTP_TIMEOUT_SECONDS,
        allowed_origins: Optional[Sequence[str]] = None,
    ) -> None:
        if not isinstance(token, str) or not token or "\r" in token or "\n" in token:
            raise ContractError("Shop Door bearer token is required")
        origin = _origin(api_base)
        if isinstance(allowed_origins, (str, bytes)):
            raise ContractError(
                "Shop Door allowed_origins must be a sequence of HTTPS origins"
            )
        allowed = {
            _origin(item) for item in (allowed_origins or (DEFAULT_SHOP_API,))
        }
        if origin not in allowed:
            raise ContractError(
                "Shop Door API origin %s is not pinned in allowed_origins" % origin
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
            raise ContractError("Shop Door timeout_seconds must be a positive integer")
        self.timeout_seconds = timeout_seconds

    def _request(
        self,
        method: str,
        path: str,
        body: Optional[bytes] = None,
        content_type: Optional[str] = None,
    ) -> HttpResponse:
        # Cloudflare rejects urllib's implicit ``Python-urllib/*`` signature
        # before the request reaches the Shop API (Error 1010).  Give every
        # shared Shop request a stable, honest Workshop identity instead.
        headers = {
            "Authorization": "Bearer %s" % self._token,
            "Accept": "application/json",
            "User-Agent": SHOP_USER_AGENT,
        }
        if content_type:
            headers["Content-Type"] = content_type
        return self.transport(
            method,
            self.api_base + path,
            headers,
            body,
            self.timeout_seconds,
        )

    def import_design(
        self,
        packet: Path,
        metadata: Mapping[str, Any],
        *,
        thumbnail: Optional[Mapping[str, Any]] = None,
    ) -> HttpResponse:
        packet = Path(packet)
        content = _load_pack(packet)[0]
        return self.import_design_bytes(
            packet.name, content, metadata, thumbnail=thumbnail
        )

    def import_design_bytes(
        self,
        filename: str,
        content: bytes,
        metadata: Mapping[str, Any],
        *,
        thumbnail: Optional[Mapping[str, Any]] = None,
    ) -> HttpResponse:
        filename = _validate_upload_filename(filename)
        content = _validate_pack_bytes(content)[0]
        normalized_thumbnail = _normalize_import_thumbnail(thumbnail)
        metadata = _normalize_shop_listing(
            metadata, allow_workshop_fields=True
        )
        fields = [("status", "draft")]
        for name in ("title", "description", "category", "prompt", "license"):
            if metadata.get(name) is not None:
                fields.append((name, str(metadata[name])))
        tags = metadata["tags"]
        if tags:
            for tag in tags:
                fields.append(("tags", str(tag)))
        else:
            # The backend distinguishes an absent tag field (derive defaults)
            # from a present empty field (the exact requested empty set).
            fields.append(("tags", ""))
        content_type = mimetypes.guess_type(filename)[0] or "application/zip"
        files = [("file", filename, content_type, content)]
        if normalized_thumbnail is not None:
            files.append(
                (
                    "thumbnails",
                    normalized_thumbnail["filename"],
                    normalized_thumbnail["content_type"],
                    normalized_thumbnail["content"],
                )
            )
        body, multipart_type = _multipart(fields, files)
        return self._request("POST", "/designs/import", body, multipart_type)

    def get_design(self, slug: str) -> HttpResponse:
        return self._request("GET", "/designs/%s" % urllib.parse.quote(slug, safe=""))

    def upload_file_bytes(
        self,
        filename: str,
        content: bytes,
        content_type: Optional[str] = None,
    ) -> HttpResponse:
        filename = _validate_upload_filename(filename)
        if type(content) is not bytes or not content or len(content) > MAX_UPLOAD_BYTES:
            raise ContractError("Shop media must be 1 byte..50 MB of immutable bytes")
        assert_packable_content(filename, content)
        selected_type = content_type or mimetypes.guess_type(filename)[0]
        selected_type = selected_type or "application/octet-stream"
        if (
            not isinstance(selected_type, str)
            or not selected_type
            or len(selected_type) > 200
            or "\r" in selected_type
            or "\n" in selected_type
        ):
            raise ContractError("Shop media content type is malformed")
        body, multipart_type = _multipart(
            (), (("file", filename, selected_type, content),)
        )
        return self._request("POST", "/uploads", body, multipart_type)

    def patch_use_case(
        self, slug: str, use_case: Mapping[str, Any]
    ) -> HttpResponse:
        body = json.dumps(
            _normalize_use_case(use_case),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        return self._request(
            "PATCH",
            "/designs/%s/use-case" % urllib.parse.quote(slug, safe=""),
            body,
            "application/json",
        )

    def put_story_blocks(
        self, slug: str, story_blocks: Sequence[Mapping[str, Any]]
    ) -> HttpResponse:
        body = json.dumps(
            {"story_blocks": _normalize_story_blocks(story_blocks)},
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        return self._request(
            "PUT",
            "/designs/%s/story-blocks" % urllib.parse.quote(slug, safe=""),
            body,
            "application/json",
        )

    def publish(
        self,
        slug: str,
        price_cents: Optional[int] = None,
        *,
        title: Optional[str] = None,
        attachments: Sequence[Mapping[str, Any]] = (),
    ) -> HttpResponse:
        if price_cents is not None and (
            not isinstance(price_cents, int)
            or isinstance(price_cents, bool)
            or not 100 <= price_cents <= 1_000_000
        ):
            raise ContractError(
                "price_cents must be an integer in the Shop Door's 100..1000000 range"
            )
        if title is not None and (
            not isinstance(title, str)
            or not title.strip()
            or len(title) > 120
            or any(ord(character) < 32 or ord(character) == 127 for character in title)
        ):
            raise ContractError("Shop publish title must be 1..120 control-free characters")
        normalized_attachments = _normalize_attachments(attachments)
        request: Dict[str, Any] = {}
        if title is not None:
            request["title"] = title
        if price_cents is not None:
            request["listing"] = {"price_cents": price_cents}
        if normalized_attachments:
            request["attachments"] = normalized_attachments
        path = "/designs/%s/publish" % urllib.parse.quote(slug, safe="")
        if not request:
            return self._request("POST", path)
        body = json.dumps(
            request,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        return self._request(
            "POST", path, body, "application/json"
        )

    def unpublish(self, slug: str) -> HttpResponse:
        return self._request(
            "POST",
            "/designs/%s/unpublish" % urllib.parse.quote(slug, safe=""),
            b"{}",
            "application/json",
        )


class _ShopSender:
    """Durable Shop sender; every remote effect is recorded before sending."""

    def __init__(self, store: InventorStore, client: ShopDoor, owner_id: str) -> None:
        if not isinstance(owner_id, str) or not owner_id:
            raise ContractError("Shop owner_id is required")
        self.store = store
        self.client = client
        self.owner_id = owner_id

    def import_draft(
        self,
        product_id: str,
        packet: Path,
        metadata: Mapping[str, Any],
        lease_token: Optional[str] = None,
        *,
        inventor_name: Optional[str] = None,
        instructions_sha256: Optional[str] = None,
        playtest_evidence_sha256: Optional[str] = None,
        thumbnail: Optional[Mapping[str, Any]] = None,
    ) -> PublicationOutcome:
        packet = Path(packet)
        metadata = _normalize_shop_listing(
            metadata, inventor_name=inventor_name
        )
        packet_bytes, packet_sha, artifact_sha = _load_pack(packet)
        _assert_shop_importable_pack(packet_bytes)
        normalized_thumbnail = _normalize_import_thumbnail(thumbnail)
        _validate_upload_filename(packet.name)
        product = self.store.get_product(product_id)
        if not product.get("artifact_sha256"):
            raise ContractError("product must bind exact artifact bytes before publication")
        if product["artifact_sha256"] != artifact_sha:
            raise ContractError(
                "Pack artifact does not match the product's selected artifact"
            )
        request = dict(metadata)
        request["_workshop_artifact_sha256"] = artifact_sha
        request["_workshop_owner_id"] = self.owner_id
        request["_workshop_api_origin"] = self.client.api_origin
        if instructions_sha256 is not None:
            request["_workshop_instructions_sha256"] = require_sha256(
                instructions_sha256, "Instructions sha256"
            )
        if playtest_evidence_sha256 is not None:
            request["_workshop_playtest_evidence_sha256"] = require_sha256(
                playtest_evidence_sha256, "Playtest evidence sha256"
            )
        if normalized_thumbnail is not None:
            request.update(
                {
                    "_workshop_cover_filename": normalized_thumbnail["filename"],
                    "_workshop_cover_content_type": normalized_thumbnail["content_type"],
                    "_workshop_cover_bytes": len(normalized_thumbnail["content"]),
                    "_workshop_cover_sha256": normalized_thumbnail["sha256"],
                }
            )
        intent = self.store.prepare_publish(
            product_id,
            packet_sha,
            request,
            remote_slug_hint=None,
            lease_token=lease_token,
        )
        if intent["state"] in ("succeeded", "live"):
            receipt = PublicationReceipt.from_dict(intent["receipt"])
            receipt.assert_owner(self.owner_id)
            receipt.assert_artifact(artifact_sha)
            return PublicationOutcome(intent["id"], receipt)
        if intent["state"] == "live_unknown":
            receipt = self.reconcile_live(intent["id"])
            receipt.assert_artifact(artifact_sha)
            return PublicationOutcome(intent["id"], receipt)
        intent = self.store.begin_publish(intent["id"], lease_token=lease_token)
        effect_token = intent["effect_token"]
        try:
            response = self.client.import_design_bytes(
                packet.name,
                packet_bytes,
                intent["request"],
                thumbnail=normalized_thumbnail,
            )
        except Exception as exc:
            self.store.mark_publish_unknown(
                intent["id"], effect_token, "%s: %s" % (type(exc).__name__, exc)
            )
            raise AmbiguousPublishError(
                "Shop import outcome is unknown; intent %s must be reconciled before retry"
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
                    "Shop Door rejected import (HTTP %s): %s" % (response.status, summary)
                )
            self.store.mark_publish_unknown(
                intent["id"],
                effect_token,
                "HTTP %s: %s" % (response.status, summary),
            )
            raise AmbiguousPublishError(
                "Shop Door import returned HTTP %s; reconcile intent %s before retry"
                % (response.status, intent["id"])
            )
        try:
            design = _json_body(response)
            receipt = PublicationReceipt.from_design(design, packet_sha, artifact_sha)
            receipt.assert_owner(self.owner_id)
            if receipt.status != "draft":
                raise ReceiptError("Shop Door did not return the required draft state")
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
                "Shop Door accepted import but no valid Stamp was recorded; reconcile intent %s"
                % intent["id"]
            ) from exc

    def reconcile_import(self, intent_id: str, remote_slug: str) -> PublicationReceipt:
        """Fail closed until the Shop Door exposes remote content identity."""
        del remote_slug
        intent = self.store.get_publish_intent(intent_id)
        if intent["state"] != "unknown":
            raise PublishError("intent %s is not awaiting import reconciliation" % intent_id)
        raise AmbiguousPublishError(
            "Shop Door readback does not expose a Pack/tree hash, so a slug cannot prove "
            "which bytes created intent %s; backend idempotency support is required"
            % intent_id
        )

    def publish_live(
        self,
        intent_id: str,
        price_cents: Optional[int] = None,
        lease_token: Optional[str] = None,
        *,
        title: Optional[str] = None,
        attachments: Sequence[Mapping[str, Any]] = (),
        proof: Optional[Mapping[str, Any]] = None,
    ) -> PublicationReceipt:
        if price_cents is not None and (
            not isinstance(price_cents, int)
            or isinstance(price_cents, bool)
            or not 100 <= price_cents <= 1_000_000
        ):
            raise ContractError(
                "price_cents must be an integer in the Shop Door's 100..1000000 range"
            )
        if title is not None and (
            not isinstance(title, str)
            or not title.strip()
            or len(title) > 120
            or any(ord(character) < 32 or ord(character) == 127 for character in title)
        ):
            raise ContractError("Shop publish title must be 1..120 control-free characters")
        # Build the complete request before checking for a completed intent so
        # replay means exact idempotency, never silent acceptance of a new price,
        # attachment set, title, or proof under an old receipt.
        live_request: Dict[str, Any] = {
            "api_origin": self.client.api_origin,
            "owner_id": self.owner_id,
        }
        if price_cents is not None:
            live_request["listing"] = {"price_cents": price_cents}
        if title is not None:
            live_request["title"] = title
        normalized_attachments = _normalize_attachments(attachments)
        if normalized_attachments:
            live_request["attachments"] = normalized_attachments
        if proof is not None:
            live_request["proof"] = dict(proof)
        intent = self.store.get_publish_intent(intent_id)
        if intent["state"] == "live":
            persisted_request = intent.get("live_request")
            if (
                not isinstance(persisted_request, Mapping)
                or _canonical_sha256(persisted_request)
                != _canonical_sha256(live_request)
            ):
                raise StateConflict(
                    "live Shop request changed under a completed intent"
                )
            return PublicationReceipt.from_dict(intent["receipt"])
        if intent["state"] != "succeeded":
            raise AmbiguousPublishError(
                "intent %s is %s, not a proven draft" % (intent_id, intent["state"])
            )
        draft = PublicationReceipt.from_dict(intent["receipt"])
        draft.assert_owner(self.owner_id)
        # Persist an intermediate state before the second non-idempotent-facing effect.
        intent = self.store.begin_live(intent_id, live_request, lease_token=lease_token)
        effect_token = intent["effect_token"]
        try:
            persisted = intent["live_request"]
            listing = persisted.get("listing")
            response = self.client.publish(
                draft.slug,
                listing.get("price_cents") if isinstance(listing, Mapping) else None,
                title=persisted.get("title"),
                attachments=persisted.get("attachments") or (),
            )
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
                    "Shop Door rejected publication (HTTP %s): %s"
                    % (response.status, summary)
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
        draft = PublicationReceipt.from_dict(intent["receipt"])
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
            design = _json_body(response)
            receipt = PublicationReceipt.from_design(
                _design_with_normalized_currency(design),
                draft.packet_sha256,
                draft.artifact_sha256,
            )
            receipt.assert_owner(self.owner_id)
            intent = self.store.get_publish_intent(intent_id)
            live_request = intent.get("live_request")
            if not isinstance(live_request, Mapping):
                raise ReceiptError("publish intent lacks its persisted live request")
            draft_request = intent.get("request")
            if (
                isinstance(draft_request, Mapping)
                and draft_request.get("_workshop_instructions_sha256") is not None
                and (
                    design.get("title") != draft_request.get("title")
                    or design.get("description") != draft_request.get("description")
                )
            ):
                raise ReceiptError(
                    "public readback does not contain the sealed Instructions title and summary"
                )
            listing_request = live_request.get("listing")
            if listing_request is not None and not isinstance(listing_request, Mapping):
                raise ReceiptError("publish intent has a malformed listing request")
            if isinstance(listing_request, Mapping):
                receipt.assert_listing(listing_request.get("price_cents"))
            expected_attachments = live_request.get("attachments") or []
            observed_attachments = design.get("attachments") or []
            if not isinstance(observed_attachments, list):
                raise ReceiptError("public readback attachments are malformed")
            projected_attachments = []
            for item in observed_attachments:
                if not isinstance(item, Mapping):
                    raise ReceiptError("public readback attachment is malformed")
                projected_attachments.append(
                    {"kind": item.get("kind"), "url": item.get("url")}
                )
            if projected_attachments != expected_attachments:
                raise ReceiptError(
                    "public readback does not contain the exact Instructions media"
                )
            for page_effect in self.store.shop_effects_for_publish_intent(intent_id):
                if page_effect.get("kind") not in ("use-case", "story-blocks"):
                    continue
                effect_request = page_effect.get("request")
                if (
                    page_effect.get("state") != "succeeded"
                    or not isinstance(effect_request, Mapping)
                    or not ShopInstructionsWriter._content_matches(
                        page_effect["kind"], design, effect_request.get("content")
                    )
                ):
                    raise ReceiptError(
                        "public readback does not contain the sealed Instructions copy"
                    )
            renamed = live_request.get("title") is not None
            if (
                receipt.design_id != draft.design_id
                or receipt.root_id != draft.root_id
                or receipt.current_history_id != draft.current_history_id
                or (
                    not renamed
                    and (
                        receipt.slug != draft.slug
                        or receipt.project_url != draft.project_url
                    )
                )
            ):
                raise ReceiptError("public readback does not identify the exact draft history")
            proof = live_request.get("proof")
            if isinstance(proof, Mapping):
                receipt = _receipt_with_details(receipt, proof)
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


class ShopInstructionsWriter:
    """Shared Instructions-to-site adapter inherited by every inventor.

    ``DefaultInstructions`` seals the box paper and product-page document, then
    calls this object as ``writer(context, root, manifest)``.  This adapter
    imports the exact Made artifact as a private draft, uploads the five sealed
    views, applies optional curated page sections, and returns authenticated
    private-draft readback bound to both Made and Instructions bytes.  It never
    makes the page public: that customer-visible transition belongs to a later,
    explicit owner action.
    """

    def __init__(
        self,
        store: InventorStore,
        client: ShopDoor,
        owner_id: str,
        *,
        price_cents: Optional[int] = None,
    ) -> None:
        if price_cents is not None:
            raise ContractError(
                "Shop Instructions creates a private draft; price_cents belongs "
                "to the separate owner-controlled public transition"
            )
        self.store = store
        self.client = client
        self.owner_id = owner_id
        self._sender = _ShopSender(store, client, owner_id)

    @staticmethod
    def _assert_sealed(root: Path, manifest: ArtifactManifest) -> Path:
        requested = Path(root)
        if (
            not requested.is_absolute()
            or requested.is_symlink()
            or not requested.is_dir()
            or not isinstance(manifest, ArtifactManifest)
        ):
            raise ContractError(
                "Shop Instructions require an absolute sealed Instructions directory"
            )
        resolved = requested.resolve(strict=True)
        current = build_artifact_manifest(resolved, created_at=manifest.created_at)
        if current.to_dict() != manifest.to_dict():
            raise ContractError("Instructions bytes changed after they were sealed")
        return resolved

    @staticmethod
    def _read_page(root: Path) -> Mapping[str, Any]:
        path = root / "product.json"
        if path.is_symlink() or not path.is_file():
            raise ContractError("sealed Instructions require product.json")
        content = path.read_bytes()
        page = _json_body(HttpResponse(200, {}, content))
        required = {
            "title",
            "summary",
            "lane",
            "images",
            "product_artifact_sha256",
            "playtest_evidence_artifact_sha256",
        }
        if not required <= set(page):
            raise ContractError("sealed product.json is missing required page fields")
        return page

    @staticmethod
    def _read_media(
        root: Path,
        manifest: ArtifactManifest,
        page: Mapping[str, Any],
    ) -> Mapping[str, Mapping[str, Any]]:
        images = page.get("images")
        if not isinstance(images, Mapping) or set(images) != set(SHOP_INSTRUCTIONS_IMAGES):
            raise ContractError(
                "Shop Instructions require hero, play, detail, parts, and box images"
            )
        manifest_entries = {entry.path: entry for entry in manifest.entries}
        media: Dict[str, Mapping[str, Any]] = {}
        for role in SHOP_INSTRUCTIONS_IMAGES:
            relative = images.get(role)
            candidate = Path(relative) if isinstance(relative, str) else Path(".")
            if (
                not isinstance(relative, str)
                or not relative
                or candidate.is_absolute()
                or ".." in candidate.parts
                or "\\" in relative
                or candidate.as_posix() != relative
            ):
                raise ContractError("Instructions image %s has an unsafe path" % role)
            path = root / candidate
            try:
                resolved = path.resolve(strict=True)
                resolved.relative_to(root)
            except (OSError, ValueError) as exc:
                raise ContractError("Instructions image %s is missing" % role) from exc
            if path.is_symlink() or not resolved.is_file():
                raise ContractError("Instructions image %s is not a regular file" % role)
            entry = manifest_entries.get(relative)
            if entry is None:
                raise ContractError("Instructions image %s is not in the sealed manifest" % role)
            content = resolved.read_bytes()
            digest = hashlib.sha256(content).hexdigest()
            if len(content) != entry.bytes or digest != entry.sha256:
                raise ContractError("Instructions image %s changed after sealing" % role)
            content_type = mimetypes.guess_type(resolved.name)[0] or "application/octet-stream"
            if not content_type.startswith("image/"):
                raise ContractError("Instructions image %s is not an image" % role)
            media[role] = {
                "filename": resolved.name,
                "content": content,
                "content_type": content_type,
                "sha256": digest,
            }
        return media

    @staticmethod
    def _resolve_page_content(
        page: Mapping[str, Any], urls: Mapping[str, str]
    ) -> Tuple[Optional[Mapping[str, Any]], Optional[Sequence[Mapping[str, Any]]]]:
        raw_use_case = page.get("use_case")
        use_case = None
        if raw_use_case is not None:
            if not isinstance(raw_use_case, Mapping):
                raise ContractError("product.json use_case must be an object")
            image_role = raw_use_case.get("image")
            if image_role not in urls:
                raise ContractError("product.json use_case.image must name an image role")
            resolved_use_case = dict(raw_use_case)
            resolved_use_case["image"] = urls[image_role]
            use_case = _normalize_use_case(resolved_use_case)
        raw_blocks = page.get("story_blocks")
        story_blocks = None
        if raw_blocks is not None:
            if isinstance(raw_blocks, (str, bytes)) or not isinstance(raw_blocks, Sequence):
                raise ContractError("product.json story_blocks must be an array")
            resolved_blocks = []
            for index, raw in enumerate(raw_blocks):
                if not isinstance(raw, Mapping):
                    raise ContractError("product.json story_blocks[%d] is malformed" % index)
                block = dict(raw)
                hero = block.get("hero_image")
                if hero:
                    if hero not in urls:
                        raise ContractError(
                            "story_blocks[%d].hero_image must name an image role" % index
                        )
                    block["hero_image"] = urls[hero]
                pairs = block.get("pair_images", [])
                if isinstance(pairs, (str, bytes)) or not isinstance(pairs, Sequence):
                    raise ContractError(
                        "story_blocks[%d].pair_images must name image roles" % index
                    )
                try:
                    block["pair_images"] = [urls[role] for role in pairs]
                except (KeyError, TypeError) as exc:
                    raise ContractError(
                        "story_blocks[%d].pair_images must name image roles" % index
                    ) from exc
                resolved_blocks.append(block)
            story_blocks = _normalize_story_blocks(resolved_blocks)
        return use_case, story_blocks

    @staticmethod
    def _valid_upload_response(
        response: Mapping[str, Any], expected: Mapping[str, Any]
    ) -> str:
        if not isinstance(response, Mapping):
            raise ReceiptError("Shop upload response is not an object")
        url = _https_url(response.get("url"), "Shop upload URL")
        if (
            response.get("sha256") != expected["sha256"]
            or response.get("size") != len(expected["content"])
            or not isinstance(response.get("ref"), str)
            or not response.get("ref")
            or not isinstance(response.get("content_type"), str)
            or not response.get("content_type", "").startswith("image/")
        ):
            raise ReceiptError("Shop upload readback does not identify the sent image bytes")
        return url

    def _upload_media(
        self,
        intent_id: str,
        instructions_sha256: str,
        role: str,
        media: Mapping[str, Any],
        assert_current: Callable[[], None],
        lease_token: Optional[str],
    ) -> str:
        request = {
            "instructions_sha256": instructions_sha256,
            "role": role,
            "filename": media["filename"],
            "content_type": media["content_type"],
            "bytes": len(media["content"]),
            "sha256": media["sha256"],
        }
        effect = self.store.prepare_shop_effect(
            intent_id, "media-upload", role, request, lease_token
        )
        if effect["state"] == "succeeded":
            return self._valid_upload_response(effect["response"], media)
        if effect["state"] in ("sending", "unknown"):
            raise AmbiguousPublishError(
                "Instructions image upload %s is ambiguous; do not upload duplicate bytes"
                % role
            )
        effect = self.store.begin_shop_effect(effect["id"], lease_token)
        token = effect["effect_token"]
        assert_current()
        try:
            response = self.client.upload_file_bytes(
                media["filename"], media["content"], media["content_type"]
            )
        except Exception as exc:
            self.store.mark_shop_effect_unknown(
                effect["id"], token, "%s: %s" % (type(exc).__name__, exc)
            )
            raise AmbiguousPublishError(
                "Instructions image upload %s has an unknown outcome" % role
            ) from exc
        if response.status != 201:
            summary = response.body.decode("utf-8", "replace")[:500]
            if response.status in PROVEN_NO_EFFECT_STATUSES:
                self.store.mark_shop_effect_rejected(
                    effect["id"], token, "HTTP %s: %s" % (response.status, summary)
                )
                raise PublishError(
                    "Shop rejected Instructions image %s (HTTP %s)"
                    % (role, response.status)
                )
            self.store.mark_shop_effect_unknown(
                effect["id"], token, "HTTP %s: %s" % (response.status, summary)
            )
            raise AmbiguousPublishError(
                "Instructions image upload %s has an unknown outcome" % role
            )
        try:
            body = _json_body(response)
            url = self._valid_upload_response(body, media)
            self.store.mark_shop_effect_succeeded(effect["id"], token, body)
            return url
        except Exception as exc:
            try:
                current = self.store.get_shop_effect(effect["id"])
                if current["state"] == "sending":
                    self.store.mark_shop_effect_unknown(
                        effect["id"], token, "accepted upload returned malformed proof"
                    )
            except Exception:
                pass
            raise AmbiguousPublishError(
                "Shop accepted image %s without trustworthy byte proof" % role
            ) from exc

    @staticmethod
    def _content_matches(
        kind: str, observed: Mapping[str, Any], expected: Any
    ) -> bool:
        if not isinstance(observed, Mapping):
            return False
        if kind == "use-case":
            return observed.get("use_case") == expected
        return observed.get("story_blocks") == expected

    def _reconcile_content_effect(
        self,
        effect: Mapping[str, Any],
        slug: str,
        kind: str,
        expected: Any,
    ) -> Mapping[str, Any]:
        try:
            response = self.client.get_design(slug)
            if response.status == 200:
                observed = _json_body(response)
                if self._content_matches(kind, observed, expected):
                    return self.store.resolve_shop_effect_succeeded(
                        effect["id"], observed
                    )
        except Exception:
            pass
        raise AmbiguousPublishError(
            "Shop %s write is ambiguous and readback does not prove the sealed copy"
            % kind
        )

    def _write_content(
        self,
        intent_id: str,
        slug: str,
        instructions_sha256: str,
        kind: str,
        content: Any,
        assert_current: Callable[[], None],
        lease_token: Optional[str],
    ) -> None:
        request = {
            "instructions_sha256": instructions_sha256,
            "content": content,
        }
        effect = self.store.prepare_shop_effect(
            intent_id, kind, "sealed-page", request, lease_token
        )
        if effect["state"] == "succeeded":
            if not self._content_matches(kind, effect["response"], content):
                raise ReceiptError("persisted Shop content proof is malformed")
            return
        if effect["state"] == "unknown":
            self._reconcile_content_effect(effect, slug, kind, content)
            return
        if effect["state"] == "sending":
            raise AmbiguousPublishError("Shop %s effect is stranded in flight" % kind)
        effect = self.store.begin_shop_effect(effect["id"], lease_token)
        token = effect["effect_token"]
        assert_current()
        try:
            response = (
                self.client.patch_use_case(slug, content)
                if kind == "use-case"
                else self.client.put_story_blocks(slug, content)
            )
        except Exception as exc:
            unknown = self.store.mark_shop_effect_unknown(
                effect["id"], token, "%s: %s" % (type(exc).__name__, exc)
            )
            self._reconcile_content_effect(unknown, slug, kind, content)
            return
        if response.status == 200:
            try:
                observed = _json_body(response)
                if not self._content_matches(kind, observed, content):
                    raise ReceiptError("Shop content response does not match sealed copy")
                self.store.mark_shop_effect_succeeded(effect["id"], token, observed)
                return
            except Exception:
                unknown = self.store.mark_shop_effect_unknown(
                    effect["id"], token, "content response did not prove the sealed copy"
                )
                self._reconcile_content_effect(unknown, slug, kind, content)
                return
        summary = response.body.decode("utf-8", "replace")[:500]
        if response.status in PROVEN_NO_EFFECT_STATUSES:
            self.store.mark_shop_effect_rejected(
                effect["id"], token, "HTTP %s: %s" % (response.status, summary)
            )
            raise PublishError(
                "Shop rejected %s Instructions content (HTTP %s)"
                % (kind, response.status)
            )
        unknown = self.store.mark_shop_effect_unknown(
            effect["id"], token, "HTTP %s: %s" % (response.status, summary)
        )
        self._reconcile_content_effect(unknown, slug, kind, content)

    @staticmethod
    def _assert_instructions_draft_receipt(
        receipt: PublicationReceipt,
        artifact_sha256: str,
        instructions_sha256: str,
    ) -> None:
        receipt.assert_artifact(artifact_sha256)
        if not receipt.is_verified_draft:
            raise ReceiptError("Instructions require authenticated private Shop draft readback")
        _https_url(receipt.details.get("page_url"), "Shop product page URL")
        _https_url(receipt.details.get("cover_url"), "Shop draft cover URL")
        if receipt.details.get("instructions_sha256") != instructions_sha256:
            raise ReceiptError("Shop receipt is not bound to the sealed Instructions bytes")
        require_sha256(receipt.details.get("cover_sha256"), "Shop draft cover sha256")

    def _readback_draft(
        self,
        intent_id: str,
        imported: PublicationReceipt,
        proof: Mapping[str, Any],
        lease_token: Optional[str],
    ) -> PublicationReceipt:
        """Prove the enriched page still identifies the exact imported draft."""

        try:
            response = self.client.get_design(imported.slug)
        except Exception as exc:
            raise AmbiguousPublishError(
                "authenticated Instructions draft readback failed"
            ) from exc
        if response.status != 200:
            raise AmbiguousPublishError(
                "authenticated Instructions draft readback returned HTTP %s"
                % response.status
            )
        try:
            design = _json_body(response)
            receipt = PublicationReceipt.from_design(
                _design_with_normalized_currency(design),
                imported.packet_sha256,
                imported.artifact_sha256,
            )
            receipt.assert_owner(self.owner_id)
            if not receipt.is_verified_draft:
                raise ReceiptError("Shop readback no longer identifies a private draft")
            identity_fields = (
                "design_id",
                "slug",
                "owner_id",
                "root_id",
                "current_history_id",
                "project_url",
            )
            if any(
                getattr(receipt, field) != getattr(imported, field)
                for field in identity_fields
            ):
                raise ReceiptError(
                    "Shop readback does not identify the imported draft history"
                )
            intent = self.store.get_publish_intent(intent_id)
            request = intent.get("request")
            import_response = intent.get("response")
            imported_covers = (
                import_response.get("thumbnail_urls")
                if isinstance(import_response, Mapping)
                else None
            )
            observed_covers = design.get("thumbnail_urls")
            category = design.get("category")
            author = design.get("author")
            if (
                not isinstance(request, Mapping)
                or design.get("title") != request.get("title")
                or design.get("description") != request.get("description")
                or design.get("origin") != "import"
                or design.get("tags") != request.get("tags")
                or not isinstance(category, Mapping)
                or category.get("slug") != request.get("category")
                or not isinstance(imported_covers, list)
                or not imported_covers
                or observed_covers != imported_covers
                or imported_covers[0] != proof.get("cover_url")
                or (
                    isinstance(author, Mapping)
                    and author.get("id") is not None
                    and author.get("id") != self.owner_id
                )
            ):
                raise ReceiptError(
                    "Shop draft readback does not preserve the sealed Instructions import"
                )
            for page_effect in self.store.shop_effects_for_publish_intent(intent_id):
                if page_effect.get("kind") not in ("use-case", "story-blocks"):
                    continue
                effect_request = page_effect.get("request")
                if (
                    page_effect.get("state") != "succeeded"
                    or not isinstance(effect_request, Mapping)
                    or not self._content_matches(
                        page_effect["kind"], design, effect_request.get("content")
                    )
                ):
                    raise ReceiptError(
                        "Shop draft readback does not contain the sealed Instructions copy"
                    )
            receipt = _receipt_with_details(receipt, proof)
            persisted = self.store.mark_instructions_draft_ready(
                intent_id, receipt, lease_token
            )
            return PublicationReceipt.from_dict(persisted["receipt"])
        except (ContractError, PublishError, ReceiptError, StateConflict) as exc:
            raise AmbiguousPublishError(
                "authenticated Shop readback did not prove the exact Instructions draft"
            ) from exc

    def __call__(
        self,
        context: Any,
        sealed_root: Path,
        sealed_manifest: ArtifactManifest,
    ) -> PublicationReceipt:
        if not callable(getattr(context, "assert_current", None)):
            raise ContractError("ShopInstructionsWriter requires an InstructionsContext")
        context.assert_current()
        root = self._assert_sealed(sealed_root, sealed_manifest)
        instructions_sha256 = require_sha256(
            sealed_manifest.artifact_sha256, "sealed Instructions sha256"
        )
        page = self._read_page(root)
        media = self._read_media(root, sealed_manifest, page)
        # Validate every optional curated field before importing a draft or
        # uploading immutable media. Role placeholders exercise the exact same
        # copy/shape contract without creating a remote side effect.
        self._resolve_page_content(
            page,
            {
                role: "https://preflight.invalid/%s.png" % role
                for role in SHOP_INSTRUCTIONS_IMAGES
            },
        )
        artifact_sha256 = require_sha256(
            page.get("product_artifact_sha256"), "product page artifact sha256"
        )
        if artifact_sha256 != context.made.artifact_sha256:
            raise ContractError("product page describes different Made bytes")
        playtest_sha256 = require_sha256(
            page.get("playtest_evidence_artifact_sha256"),
            "product page Playtest evidence sha256",
        )
        title = page.get("title")
        summary = page.get("summary")
        lane = page.get("lane")
        if not all(isinstance(value, str) and value.strip() for value in (title, summary, lane)):
            raise ContractError("product page title, summary, and lane are required")
        product_id = context.wish.product_id
        inventor_name = context.taste.name
        lease_token = getattr(context, "lease_token", None)

        def assert_current() -> None:
            context.assert_current()
            self._assert_sealed(root, sealed_manifest)

        with tempfile.TemporaryDirectory(prefix="workshop-instructions-") as directory:
            packet = Path(directory) / "product.zip"
            build_pack(context.made.artifact_root, packet)
            assert_current()
            outcome = self._sender.import_draft(
                product_id,
                packet,
                {
                    "title": title,
                    "description": summary,
                    "category": _shop_category_for_lane(lane),
                    "tags": ["toy", lane],
                },
                inventor_name=inventor_name,
                instructions_sha256=instructions_sha256,
                playtest_evidence_sha256=playtest_sha256,
                thumbnail=media["hero"],
                lease_token=lease_token,
            )
        if outcome.receipt.details.get("instructions_sha256") is not None:
            self._assert_instructions_draft_receipt(
                outcome.receipt, artifact_sha256, instructions_sha256
            )
            return outcome.receipt
        if outcome.receipt.status != "draft":
            raise StateConflict(
                "Shop Instructions cannot reuse an intent already made public"
            )
        uploaded_urls: Dict[str, str] = {}
        for role in SHOP_INSTRUCTIONS_IMAGES:
            uploaded_urls[role] = self._upload_media(
                outcome.intent_id,
                instructions_sha256,
                role,
                media[role],
                assert_current,
                lease_token,
            )
        use_case, story_blocks = self._resolve_page_content(page, uploaded_urls)
        if use_case is not None:
            self._write_content(
                outcome.intent_id,
                outcome.receipt.slug,
                instructions_sha256,
                "use-case",
                use_case,
                assert_current,
                lease_token,
            )
        if story_blocks is not None:
            self._write_content(
                outcome.intent_id,
                outcome.receipt.slug,
                instructions_sha256,
                "story-blocks",
                story_blocks,
                assert_current,
                lease_token,
            )
        persisted_intent = self.store.get_publish_intent(outcome.intent_id)
        import_response = persisted_intent.get("response")
        cover_urls = (
            import_response.get("thumbnail_urls")
            if isinstance(import_response, Mapping)
            else None
        )
        if not isinstance(cover_urls, list) or not cover_urls:
            raise AmbiguousPublishError(
                "Shop import did not prove the sealed hero became the draft cover"
            )
        cover_url = _https_url(cover_urls[0], "Shop draft cover URL")
        proof = {
            "instructions_sha256": instructions_sha256,
            "playtest_evidence_sha256": playtest_sha256,
            "page_url": _shop_product_page_url(outcome.receipt.slug),
            "cover_sha256": media["hero"]["sha256"],
            "cover_url": cover_url,
            "media_sha256": {
                role: media[role]["sha256"] for role in SHOP_INSTRUCTIONS_IMAGES
            },
            "page_content_sha256": _canonical_sha256(page),
        }
        assert_current()
        receipt = self._readback_draft(
            outcome.intent_id,
            outcome.receipt,
            proof,
            lease_token,
        )
        self._assert_instructions_draft_receipt(
            receipt, artifact_sha256, instructions_sha256
        )
        return receipt
