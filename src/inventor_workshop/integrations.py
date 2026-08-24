"""Small, ordinary boundaries around external effects.

An adapter is deliberately not a Workshop lifecycle concept.  It is simply
the implementation supplied to :class:`~inventor_workshop.runtime.Runtime`
when work must cross a process or service boundary.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Mapping, Optional, Protocol

if TYPE_CHECKING:
    from .models import Receipt
    from .pack import Artifact


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


__all__ = ["Adapter"]
