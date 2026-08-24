"""Workshop 0.2 launch compatibility; new code uses Pack, ShopDoor, and Sender."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from .pack import _inspect_pack_details, _load_pack, _validate_pack_bytes
from .shop import (
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
_load_packet = _load_pack
_validate_packet_bytes = _validate_pack_bytes


def inspect_publish_packet(packet: Path) -> Dict[str, Any]:
    """Compatibility wrapper returning the former packet digest key."""

    details = dict(_inspect_pack_details(Path(packet)))
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
