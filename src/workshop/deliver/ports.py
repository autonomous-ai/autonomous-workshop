"""Fulfillment port declared by Deliver and implemented by integrations."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Mapping, Optional, Protocol

if TYPE_CHECKING:
    from workshop.artifacts import Artifact
    from workshop.runtime import Stamp


class DeliveryPort(Protocol):
    """Quote a material-specific handoff for exact product artifact bytes."""

    def quote(self, artifact_root: Path, material: str) -> Mapping[str, Any]:
        ...


class DeliveryDoor(Protocol):
    """Quote or hand off an exact Artifact to printing and fulfillment."""

    name: str

    def quote(self, artifact_root: Path, material: str) -> Mapping[str, Any]:
        ...

    def deliver(
        self,
        packed: "Artifact",
        request: Mapping[str, Any],
        effect_token: str,
    ) -> "Stamp":
        ...

    def reconcile(self, intent: Mapping[str, Any]) -> Optional["Stamp"]:
        ...


__all__ = ["DeliveryDoor", "DeliveryPort"]
