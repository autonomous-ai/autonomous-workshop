"""Compatibility protocols for integrations formerly called Doors.

New generic integrations implement :class:`inventor_workshop.integrations.Adapter`.
The domain-specific protocols below remain import-compatible for existing
inventors while their call sites migrate to ordinary adapter terminology.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Mapping, Optional, Protocol, Sequence

from .cad import CadReleaseBundle
from .integrations import Adapter
from .models import InspectionResult

if TYPE_CHECKING:
    from .shop import HttpResponse
    from .make import CadBuildResult, Wish
    from .models import Stamp
    from .pack import PackedArtifact


class ModelDoor(Protocol):
    """Run one bounded model or agent role."""

    def run(
        self,
        role: str,
        request: Mapping[str, Any],
        budget_micros: int,
    ) -> Mapping[str, Any]:
        ...


class CadDoor(Protocol):
    """Turn an accepted concept into product artifact files."""

    def build(
        self,
        wish: "Wish",
        concept: Mapping[str, Any],
        workspace: Path,
    ) -> "CadBuildResult":
        ...


class CadInspectionDoor(Protocol):
    """Verify CAD and manufacturing evidence for exact artifact bytes."""

    def verify(
        self,
        artifact_root: Path,
        artifact_sha256: str,
    ) -> CadReleaseBundle:
        ...


class InspectionDoor(Protocol):
    """Return artifact-bound domain Inspection results."""

    def inspect(
        self,
        artifact_root: Path,
        artifact_sha256: str,
    ) -> Sequence[InspectionResult]:
        ...


class ShopDoorProtocol(Protocol):
    """Optional shop transport used by :class:`~inventor_workshop.Sender`."""

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


class SendDoor(Protocol):
    """Send one exact Pack and return authenticated, durable evidence."""

    name: str

    def send(
        self,
        packed: "PackedArtifact",
        request: Mapping[str, Any],
        effect_token: str,
    ) -> "Stamp":
        ...

    def reconcile(self, intent: Mapping[str, Any]) -> Optional["Stamp"]:
        ...


class DeliveryDoor(Protocol):
    """Quote or hand off a Pack to printing and fulfillment."""

    name: str

    def quote(self, artifact_root: Path, material: str) -> Mapping[str, Any]:
        ...

    def deliver(
        self,
        packed: "PackedArtifact",
        request: Mapping[str, Any],
        effect_token: str,
    ) -> "Stamp":
        ...

    def reconcile(self, intent: Mapping[str, Any]) -> Optional["Stamp"]:
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
