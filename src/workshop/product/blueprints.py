"""Immutable lane bindings enforced by the Workshop host.

Creative recipes belong to the product-run skill and the selected Inventor.
Python records only the lane identity and the exact Playtest checks required to
bind Match, Make, and Playtest to the same deterministic contract.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from workshop.errors import ContractError


PLAYTHING_LANES = (
    "classics-made-yours",
    "invented-games",
    "moving-machines",
    "holdable-science",
    "little-worlds",
)

_LANE_PLAYTEST_CHECK = MappingProxyType(
    {
        "classics-made-yours": "classic-rules-test",
        "invented-games": "game-simulation",
        "moving-machines": "motion-test",
        "holdable-science": "science-test",
        "little-worlds": "world-test",
    }
)


@dataclass(frozen=True)
class ToyBlueprint:
    """Canonical lane and host-required Playtest check ids."""

    lane: str
    playtest_check_ids: tuple[str, ...] = field(init=False)

    def __post_init__(self) -> None:
        try:
            lane_check = _LANE_PLAYTEST_CHECK[self.lane]
        except (KeyError, TypeError):
            raise ContractError(
                "plaything lane must be one of %s" % ", ".join(PLAYTHING_LANES)
            ) from None
        object.__setattr__(
            self,
            "playtest_check_ids",
            ("agent-playtest", lane_check, "mechanical-test", "print-test"),
        )

    @classmethod
    def for_lane(cls, lane: str) -> "ToyBlueprint":
        return cls(lane)

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

    def required_capabilities(self, stage: str) -> tuple[str, ...]:
        if stage != "playtest":
            raise ContractError("toy blueprint defines only Playtest capabilities")
        return self.playtest_check_ids

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "kind": "autonomous-workshop.toy-blueprint",
            "lane": self.lane,
            "required_playtest_checks": list(self.playtest_check_ids),
        }


__all__ = ["PLAYTHING_LANES", "ToyBlueprint"]
