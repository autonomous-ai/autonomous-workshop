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
# Round scores are Codex-authored evidence: at least SCORE_MINIMUM_READS
# independent readers score the sealed revision 0..SCORE_MAXIMUM on each
# dimension inside the agent-playtest check.  The host only computes the
# median and spread and refuses a `pass` whose medians sit below the floor.
# These are not part of to_dict(), so the blueprint hash bound into sealed
# contracts is unchanged.
SCORE_DIMENSIONS = ("wish_fit", "play", "legibility", "build_confidence")
SCORE_FLOOR = 5
SCORE_MAXIMUM = 10
SCORE_MINIMUM_READS = 3
SCORE_AMBIGUOUS_SPREAD = 3


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

    def score_dimensions(self) -> tuple[str, ...]:
        """Dimensions independent Playtest readers score, 0 to 10 each."""

        return SCORE_DIMENSIONS

    def score_floor(self) -> int:
        """The median below which a revision cannot pass Playtest."""

        return SCORE_FLOOR

    def score_minimum_reads(self) -> int:
        return SCORE_MINIMUM_READS

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 2,
            "kind": "autonomous-workshop.toy-blueprint",
            "required_playtest_checks": list(self.playtest_check_ids),
        }


__all__ = [
    "BASELINE_PLAYTEST_CHECKS",
    "SCORE_AMBIGUOUS_SPREAD",
    "SCORE_DIMENSIONS",
    "SCORE_FLOOR",
    "SCORE_MAXIMUM",
    "SCORE_MINIMUM_READS",
    "ToyBlueprint",
]
