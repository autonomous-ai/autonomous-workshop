"""Low-level HTTP client for the current Shop Door.

The current Shop Door import endpoint creates drafts but is not idempotent. This
client therefore never retries an ambiguous import. Automatic live publication
is available only after the server advertises the hash-bound v1 capabilities
required by Alice's release policy.
"""

from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import secrets
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from .page import (
    ALICE_PRODUCT_DESCRIPTION_SUFFIX,
    has_exact_alice_product_description_suffix,
)


MAX_ARCHIVE_BYTES = 95 * 1024 * 1024
REQUIRED_LIVE_CAPABILITIES = frozenset(
    {
        "idempotent_import",
        "packet_hash_bound_publish",
        "explicit_price",
        "order_to_print_job",
    }
)


class ShopDoorError(RuntimeError):
    pass


class AmbiguousShopDoorEffect(ShopDoorError):
    """The request may have committed remotely; the caller must reconcile."""


class _RejectRedirects(urllib.request.HTTPRedirectHandler):
    """Do not forward Shop Door bearer credentials across HTTP redirects."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        return None


@dataclass(frozen=True, slots=True)
class ShopDraftStamp:
    import_key: str
    request_sha256: str
    design_id: str
    slug: str
    status: str
    history_id: str
    project_url: str | None
    archive_sha256: str
    raw: dict[str, Any]


@dataclass(frozen=True, slots=True)
class ShopSendStamp:
    design_id: str
    slug: str
    status: str
    packet_hash: str
    policy_hash: str
    price: dict[str, Any]
    url: str | None
    raw: dict[str, Any]


class ShopDoorClient:
    def __init__(
        self,
        base_url: str,
        token: str,
        *,
        timeout_seconds: int = 180,
    ) -> None:
        parsed = urllib.parse.urlsplit(base_url)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError(
                "Shop Door base_url must be a credential-free HTTPS origin/path"
            )
        if not token:
            raise ValueError("Shop Door bearer token is required")
        self.base_url = base_url.rstrip("/")
        self._token = token
        self.timeout_seconds = timeout_seconds
        self._opener = urllib.request.build_opener(_RejectRedirects())

    def __repr__(self) -> str:
        return (
            f"ShopDoorClient(base_url={self.base_url!r}, "
            f"timeout_seconds={self.timeout_seconds!r}, token=<redacted>)"
        )

    @classmethod
    def from_environment(
        cls,
        base_url: str,
        token_env: str = "WORKSHOP_SHOP_TOKEN",
    ) -> "ShopDoorClient":
        token = os.environ.get(token_env)
        if token_env == "WORKSHOP_SHOP_TOKEN":
            legacy = os.environ.get("ALICE_FACTORY_TOKEN")
            if token and legacy and token != legacy:
                raise ShopDoorError(
                    "WORKSHOP_SHOP_TOKEN conflicts with its legacy token alias"
                )
            if token is None:
                token = legacy
        if not token:
            raise ShopDoorError(
                f"Shop Door token environment variable {token_env!r} is missing"
            )
        return cls(base_url, token)

    def capabilities(self) -> frozenset[str]:
        """Read capabilities from the future hash-bound Shop Door API.

        The current backend returns 404, which intentionally disables Alice's
        unattended live effect while allowing draft creation.
        """

        raw = self._json_request("GET", "/api/v1/capabilities")
        capabilities = raw.get("capabilities")
        if not isinstance(capabilities, list) or not all(
            isinstance(item, str) for item in capabilities
        ):
            raise ShopDoorError("Shop Door capabilities response is invalid")
        return frozenset(capabilities)

    def create_draft(
        self,
        archive: str | Path,
        *,
        import_key: str,
        title: str,
        description: str,
        category: str,
        tags: Sequence[str] = (),
        license_name: str = "",
        prompt: str = "",
    ) -> ShopDraftStamp:
        if not has_exact_alice_product_description_suffix(description):
            raise ValueError(
                "description must end with the exact attribution "
                f"{ALICE_PRODUCT_DESCRIPTION_SUFFIX!r} and no trailing whitespace"
            )
        archive_path = Path(archive)
        archive_bytes = archive_path.read_bytes()
        if not archive_bytes:
            raise ShopDoorError("Shop Door archive is empty")
        if len(archive_bytes) > MAX_ARCHIVE_BYTES:
            raise ShopDoorError("Shop Door archive exceeds Alice's 95 MiB safety ceiling")
        if not import_key.strip():
            raise ValueError("import_key is required")
        archive_sha256 = hashlib.sha256(archive_bytes).hexdigest()
        fields: list[tuple[str, str]] = [
            ("status", "draft"),
            ("title", title),
            ("description", description),
            ("category", category),
            ("license", license_name),
            ("prompt", prompt),
        ]
        fields.extend(("tags", tag) for tag in tags)
        body, content_type = _multipart(
            fields,
            "file",
            archive_path.name,
            archive_bytes,
            mimetypes.guess_type(archive_path.name)[0] or "application/zip",
        )
        request_sha256 = hashlib.sha256(body).hexdigest()
        headers = {
            "Content-Type": content_type,
            "Idempotency-Key": import_key,
            "X-Alice-Archive-SHA256": archive_sha256,
        }
        try:
            raw = self._request("POST", "/api/v1/designs/import", body=body, headers=headers)
        except (TimeoutError, urllib.error.URLError) as exc:
            raise AmbiguousShopDoorEffect(
                "Shop Door import timed out or disconnected; reconcile before any retry"
            ) from exc
        status = str(raw.get("status", ""))
        if status != "draft":
            raise ShopDoorError(f"Shop Door send did not remain a draft: {status!r}")
        design_id = str(raw.get("id") or "")
        slug = str(raw.get("slug") or "")
        history_id = str(raw.get("current_history_id") or "")
        if not design_id or not slug or not history_id:
            raise ShopDoorError("Shop draft stamp lacks id, slug, or current_history_id")
        if raw.get("published_history_id"):
            raise ShopDoorError("Shop draft unexpectedly has a published history")
        return ShopDraftStamp(
            import_key=import_key,
            request_sha256=request_sha256,
            design_id=design_id,
            slug=slug,
            status=status,
            history_id=history_id,
            project_url=str(raw["project_url"]) if raw.get("project_url") else None,
            archive_sha256=archive_sha256,
            raw=raw,
        )

    def get_design(self, slug: str) -> dict[str, Any]:
        design = self._json_request(
            "GET", f"/api/v1/designs/{urllib.parse.quote(slug)}"
        )
        if not has_exact_alice_product_description_suffix(
            design.get("description")
        ):
            raise ShopDoorError(
                "Shop Door design description lacks Alice's exact attribution"
            )
        return design

    def request_slice(self, stamp: ShopDraftStamp) -> dict[str, Any]:
        """Queue slicing once. Poll with get_slice; never repeat this request."""

        return self._json_request(
            "POST", f"/api/v1/designs/{urllib.parse.quote(stamp.slug)}/slice", payload={}
        )

    def get_slice(self, stamp: ShopDraftStamp) -> dict[str, Any]:
        return self._json_request(
            "GET", f"/api/v1/designs/{urllib.parse.quote(stamp.slug)}/slice"
        )

    def publish_live(
        self,
        stamp: ShopDraftStamp,
        *,
        packet_hash: str,
        policy_hash: str,
        price: Mapping[str, Any],
    ) -> ShopSendStamp:
        capabilities = self.capabilities()
        missing = REQUIRED_LIVE_CAPABILITIES - capabilities
        if missing:
            raise ShopDoorError(
                "Shop Door cannot safely send; missing capabilities: "
                + ", ".join(sorted(missing))
            )
        payload = {
            "idempotency_key": f"alice:publish:{stamp.design_id}:{packet_hash}",
            "expected_history_id": stamp.history_id,
            "packet_hash": packet_hash,
            "policy_hash": policy_hash,
            "price": dict(price),
            "fulfillment": "print_on_demand",
        }
        raw = self._json_request(
            "POST",
            f"/api/v1/designs/{urllib.parse.quote(stamp.slug)}/publish",
            payload=payload,
        )
        status = str(raw.get("status", ""))
        if status not in {"published", "exists"}:
            raise ShopDoorError(f"Shop Door did not confirm send: {status!r}")
        if raw.get("packet_hash") != packet_hash:
            raise ShopDoorError("Shop send stamp packet_hash mismatch")
        if raw.get("policy_hash") != policy_hash:
            raise ShopDoorError("Shop send stamp policy_hash mismatch")
        return ShopSendStamp(
            design_id=stamp.design_id,
            slug=stamp.slug,
            status=status,
            packet_hash=packet_hash,
            policy_hash=policy_hash,
            price=dict(price),
            url=str(raw["url"]) if raw.get("url") else None,
            raw=raw,
        )

    def _json_request(
        self, method: str, path: str, payload: Mapping[str, Any] | None = None
    ) -> dict[str, Any]:
        body = None
        headers: dict[str, str] = {}
        if payload is not None:
            body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
            headers["Content-Type"] = "application/json"
        return self._request(method, path, body=body, headers=headers)

    def _request(
        self,
        method: str,
        path: str,
        *,
        body: bytes | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        request_headers = {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/json",
            "User-Agent": "alice-inventor/0.1",
            **dict(headers or {}),
        }
        request = urllib.request.Request(
            f"{self.base_url}{path}", data=body, method=method, headers=request_headers
        )
        try:
            with self._opener.open(request, timeout=self.timeout_seconds) as response:
                response_body = response.read()
        except urllib.error.HTTPError as exc:
            detail_sha256 = hashlib.sha256(exc.read()).hexdigest()
            raise ShopDoorError(
                f"Shop Door HTTP {exc.code}; response_body_sha256={detail_sha256}"
            ) from exc
        try:
            raw = json.loads(response_body)
        except json.JSONDecodeError as exc:
            raise ShopDoorError("Shop Door returned invalid JSON") from exc
        if not isinstance(raw, dict):
            raise ShopDoorError("Shop Door response must be an object")
        return raw


def _multipart(
    fields: Sequence[tuple[str, str]],
    file_field: str,
    filename: str,
    file_bytes: bytes,
    mime_type: str,
) -> tuple[bytes, str]:
    boundary = f"alice-{secrets.token_hex(16)}"
    chunks: list[bytes] = []
    for name, value in fields:
        chunks.extend(
            (
                f"--{boundary}\r\n".encode(),
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(),
                value.encode("utf-8"),
                b"\r\n",
            )
        )
    safe_filename = filename.replace('"', "_")
    chunks.extend(
        (
            f"--{boundary}\r\n".encode(),
            (
                f'Content-Disposition: form-data; name="{file_field}"; '
                f'filename="{safe_filename}"\r\n'
            ).encode(),
            f"Content-Type: {mime_type}\r\n\r\n".encode(),
            file_bytes,
            b"\r\n",
            f"--{boundary}--\r\n".encode(),
        )
    )
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


# Compatibility imports for integrations built before Workshop 0.3.
FactoryError = ShopDoorError
AmbiguousFactoryEffect = AmbiguousShopDoorEffect
FactoryDraftReceipt = ShopDraftStamp
FactoryPublishReceipt = ShopSendStamp
FactoryClient = ShopDoorClient


__all__ = [
    "AmbiguousShopDoorEffect",
    "ShopDoorClient",
    "ShopDoorError",
    "ShopDraftStamp",
    "ShopSendStamp",
]
