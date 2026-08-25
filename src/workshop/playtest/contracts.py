"""Inputs and outputs owned by the Playtest stage."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from workshop._validation import require_sha256
from workshop.contributors import Taste
from workshop.errors import ContractError
from workshop.make import Feedback, Made
from workshop.playtest.service import Playtest
from workshop.product import ToyBlueprint
from workshop.wish import Wish


@dataclass(frozen=True)
class PlaytestContext:
    wish: Wish
    taste: Taste
    blueprint: ToyBlueprint
    round: int
    made: Made
    workspace: Path
    playtest_rounds: int = 1

    def __post_init__(self) -> None:
        if not isinstance(self.wish, Wish) or not isinstance(self.taste, Taste):
            raise ContractError("PlaytestContext requires a Wish and Taste")
        if not isinstance(self.blueprint, ToyBlueprint):
            raise ContractError("PlaytestContext requires a ToyBlueprint")
        if not isinstance(self.made, Made):
            raise ContractError("PlaytestContext requires a Made revision")
        if self.made.product["lane"] != self.blueprint.lane:
            raise ContractError("PlaytestContext product belongs to a different lane")
        if type(self.round) is not int or self.round < 1:
            raise ContractError("PlaytestContext round must be a positive integer")
        if (
            type(self.playtest_rounds) is not int
            or not 1 <= self.playtest_rounds <= 100
            or self.round > self.playtest_rounds
        ):
            raise ContractError(
                "PlaytestContext playtest_rounds must cover this round and be from 1 to 100"
            )
        root = Path(self.workspace)
        if not root.is_absolute():
            raise ContractError("PlaytestContext workspace must be absolute")
        object.__setattr__(self, "workspace", root)
        self.made.assert_current()


@dataclass(frozen=True)
class Playtested:
    """Completed evidence plus structured feedback for one exact revision."""

    evidence: Playtest
    feedback: Sequence[Feedback] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not isinstance(self.evidence, Playtest):
            raise ContractError("Playtested requires an artifact-bound Playtest")
        feedback = tuple(self.feedback)
        if not all(isinstance(item, Feedback) for item in feedback):
            raise ContractError("Playtested feedback must use Feedback records")
        object.__setattr__(self, "feedback", feedback)
        self.evidence.assert_valid()

    @property
    def passed(self) -> bool:
        return self.evidence.passed and not any(
            item.severity in ("improve", "block") for item in self.feedback
        )

    def assert_artifact(self, artifact_sha256: str) -> None:
        require_sha256(artifact_sha256, "Playtested artifact sha256")
        if self.evidence.artifact_sha256 != artifact_sha256:
            raise ContractError("Playtested evidence belongs to different artifact bytes")


__all__ = ["PlaytestContext", "Playtested"]
