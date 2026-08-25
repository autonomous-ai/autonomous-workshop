"""Cross-stage control outcomes used when work cannot proceed truthfully."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from workshop._validation import bounded_text
from workshop.errors import ContractError
from workshop.product import WORKSHOP_JOBS


@dataclass(frozen=True)
class Need:
    """A truthful request for a capability or real-world evidence."""

    job: str
    capability: str
    reason: str
    instructions: str

    def __post_init__(self) -> None:
        if self.job not in WORKSHOP_JOBS:
            raise ContractError("need job must name one of the six Workshop jobs")
        bounded_text(self.capability, "need capability", 200)
        bounded_text(self.reason, "need reason")
        bounded_text(self.instructions, "need instructions")

    def to_dict(self) -> Dict[str, str]:
        return {
            "job": self.job,
            "capability": self.capability,
            "reason": self.reason,
            "instructions": self.instructions,
        }


class WaitingFor(RuntimeError):
    """Raised by a job when more work would otherwise fabricate evidence."""

    def __init__(self, *needs: Need) -> None:
        if not needs or not all(isinstance(item, Need) for item in needs):
            raise ContractError("WaitingFor requires at least one typed Need")
        self.needs = tuple(needs)
        super().__init__("; ".join(item.capability for item in self.needs))


__all__ = ["Need", "WaitingFor"]
