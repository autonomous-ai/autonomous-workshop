"""The random push that starts one Daydream."""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from typing import Any, Callable, Dict, Mapping, Sequence

from workshop.daydream.contracts import bounded_line
from workshop.errors import ContractError


MAX_SEED_TEXT_CHARS = 200
_SEED_KEYS = frozenset(("moment", "twist"))

SITUATIONS = (
    "a rainy Sunday at a kitchen table",
    "a long car ride with two siblings",
    "a five-minute break at a desk",
    "a dinner party waiting for dessert",
    "a grandparent and a four-year-old on a rug",
    "a quiet hour alone after work",
    "a classroom with ten minutes to spare",
    "a windowsill in the morning sun",
    "a camping table after dark",
    "a birthday party of nine-year-olds",
    "a hospital waiting room",
    "a bus stop in the cold",
    "a picnic blanket on uneven grass",
    "a bath with ten minutes of hot water left",
    "a library table where nobody may speak",
    "a train seat with a fold-down tray",
)

TWISTS = (
    "exactly one moving part",
    "the toy is also its own box",
    "it makes a sound without electronics",
    "two people need it to work",
    "it changes when flipped over",
    "gravity is the only motor",
    "it teaches a hand a new trick",
    "a game with a five-second round",
    "the pieces nest into one shape",
    "it counts something",
    "it hides something",
    "it balances on the edge of something",
    "solved by feel, not by sight",
    "it grows when you print more",
    "it can only be reset by tipping it",
    "it is played with one finger",
    "the table is part of the mechanism",
    "it ends every round in a different rest pose",
)


@dataclass(frozen=True)
class DaydreamSeed:
    """A situation and a twist: a starting push, never a requirement."""

    moment: str
    twist: str

    def __post_init__(self) -> None:
        bounded_line(self.moment, "seed moment", MAX_SEED_TEXT_CHARS)
        bounded_line(self.twist, "seed twist", MAX_SEED_TEXT_CHARS)

    @classmethod
    def parse(cls, raw: Mapping[str, Any]) -> "DaydreamSeed":
        if not isinstance(raw, Mapping) or set(raw) != _SEED_KEYS:
            raise ContractError("seed must be an object with exactly moment and twist")
        return cls(moment=raw["moment"], twist=raw["twist"])

    def to_dict(self) -> Dict[str, Any]:
        return {"moment": self.moment, "twist": self.twist}


def draw_seed(
    choose: Callable[[Sequence[str]], str] = secrets.choice,
) -> DaydreamSeed:
    """Draw one situation and one twist; ``choose`` is injectable for tests."""

    return DaydreamSeed(moment=choose(SITUATIONS), twist=choose(TWISTS))


__all__ = ["DaydreamSeed", "MAX_SEED_TEXT_CHARS", "SITUATIONS", "TWISTS", "draw_seed"]
