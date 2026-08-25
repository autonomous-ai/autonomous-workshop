"""Compatibility protocols for integrations formerly called Doors.

New generic integrations implement :class:`workshop.integrations.base.Adapter`.
The domain-specific protocols below remain import-compatible for existing
inventors while their call sites migrate to ordinary adapter terminology.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Mapping, Protocol

from workshop.deliver import DeliveryDoor
from workshop.make import CadDoor, CadInspectionDoor, InspectionDoor, ModelDoor
from workshop.runtime import Adapter, SendDoor

if TYPE_CHECKING:
    from workshop.integrations.shop import HttpResponse


class ShopDoorProtocol(Protocol):
    """Optional shop transport used by :class:`~workshop.Sender`."""

    def import_design_bytes(
        self,
        filename: str,
        content: bytes,
        metadata: Mapping[str, Any],
    ) -> "HttpResponse":
        ...

    def get_design(self, slug: str) -> "HttpResponse":
        ...

    def publish(self, slug: str, price_cents: int) -> "HttpResponse":
        ...

__all__ = [
    "Adapter",
    "CadDoor",
    "CadInspectionDoor",
    "DeliveryDoor",
    "InspectionDoor",
    "ModelDoor",
    "SendDoor",
    "ShopDoorProtocol",
]
