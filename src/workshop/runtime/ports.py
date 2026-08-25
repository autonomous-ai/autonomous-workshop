"""Generic external-effect ports declared by the durable runtime."""

from __future__ import annotations

from typing import TYPE_CHECKING, Mapping, Optional, Protocol

if TYPE_CHECKING:
    from workshop.artifacts import Artifact
    from workshop.runtime.contracts import Receipt, Stamp


class Adapter(Protocol):
    """Execute and reconcile one idempotent external effect."""

    name: str

    def execute(
        self,
        artifact: "Artifact",
        request: Mapping[str, object],
        effect_token: str,
    ) -> "Receipt":
        ...

    def reconcile(self, intent: Mapping[str, object]) -> Optional["Receipt"]:
        ...


class SendDoor(Protocol):
    """Compatibility port for adapters using the Workshop 0.3 send spelling."""

    name: str

    def send(
        self,
        packed: "Artifact",
        request: Mapping[str, object],
        effect_token: str,
    ) -> "Stamp":
        ...

    def reconcile(self, intent: Mapping[str, object]) -> Optional["Stamp"]:
        ...


__all__ = ["Adapter", "SendDoor"]
