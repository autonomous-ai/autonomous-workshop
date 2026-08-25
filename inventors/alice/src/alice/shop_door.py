"""Read/reconcile client for Alice's historical direct Shop Door boundary.

Direct draft import is retired. New models must go through Workshop's durable,
model-only Shop path so an inventor cannot upload local page media or bypass the
shared handoff contract. This client preserves authenticated readback and the
capability-gated historical publication contract for reconciliation.
"""

from __future__ import annotations

import hashlib
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from .page import has_exact_alice_product_description_suffix


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
        """Refuse the retired full-archive importer before file or network I/O.

        The signature remains for source compatibility so old callers receive
        an actionable failure. The low-level client cannot safely reconstruct
        Workshop's sealed Make identity, model-only transport Pack, durable
        intent, or authenticated Stamp, so silently delegating here would
        create a second and weaker publishing implementation.
        """
        del (
            archive,
            import_key,
            title,
            description,
            category,
            tags,
            license_name,
            prompt,
        )
        raise ShopDoorError(
            "direct ShopDoorClient.create_draft is retired: publish the "
            "inspected model through the shared Workshop model-only Shop path"
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
