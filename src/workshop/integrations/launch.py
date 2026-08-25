"""Workshop 0.2 launch compatibility; new code uses Pack, ShopDoor, and Sender."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from workshop.artifacts import (
    inspect_artifact_details,
    load_artifact_payload,
    validate_artifact_payload,
)
from workshop.integrations.shop import (
    DEFAULT_SHOP_API,
    HTTP_TIMEOUT_SECONDS,
    HttpResponse,
    PROVEN_NO_EFFECT_STATUSES,
    ShopDoor,
    Transport,
    _NoRedirectHandler,
    _ShopSender,
    urllib_transport,
)


DEFAULT_PORTAL_API = DEFAULT_SHOP_API
Portal = ShopDoor
Launchpad = _ShopSender

# Private aliases are retained for old tests/integrations that validated the
# legacy byte boundary directly. Canonical ownership lives in ``pack.py``.
_load_packet = load_artifact_payload
_validate_packet_bytes = validate_artifact_payload


def inspect_publish_packet(packet: Path) -> Dict[str, Any]:
    """Compatibility wrapper returning the former packet digest key."""

    details = dict(inspect_artifact_details(Path(packet)))
    details["packet_sha256"] = details.pop("pack_sha256")
    return details


__all__ = [
    "DEFAULT_PORTAL_API",
    "HTTP_TIMEOUT_SECONDS",
    "HttpResponse",
    "Launchpad",
    "Portal",
    "PROVEN_NO_EFFECT_STATUSES",
    "Transport",
    "inspect_publish_packet",
    "urllib_transport",
]
