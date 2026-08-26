"""Open-ended product checks enforced by the Workshop host.

Creative scope belongs to the Wish, the native Workshop Manager, and the
selected Inventor. Python binds every product to the same small baseline of
artifact-specific Playtest checks; it does not classify creativity into lanes.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any


BASELINE_PLAYTEST_CHECKS = (
    "agent-playtest",
    "mechanical-check",
    "printability-check",
)


@dataclass(frozen=True)
class ToyBlueprint:
    """Canonical open-ended host baseline for one physical product."""

    playtest_check_ids: tuple[str, ...] = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "playtest_check_ids", BASELINE_PLAYTEST_CHECKS)

    @property
    def sha256(self) -> str:
        encoded = json.dumps(
            self.to_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def required_playtest_checks(self) -> tuple[str, ...]:
        """Return the universal digital assessment baseline.

        These identifiers do not assert that a toy was printed or physically
        handled. Stronger claims require an explicit host-verifiable receipt.
        """

        return self.playtest_check_ids

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 2,
            "kind": "autonomous-workshop.toy-blueprint",
            "required_playtest_checks": list(self.playtest_check_ids),
        }


__all__ = ["BASELINE_PLAYTEST_CHECKS", "ToyBlueprint"]
