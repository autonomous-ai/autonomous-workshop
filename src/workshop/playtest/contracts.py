"""Inputs and outputs owned by the Playtest stage."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from workshop._validation import bounded_text, require_sha256
from workshop.errors import ContractError
from workshop.playtest.service import Playtest


_SEVERITIES = frozenset(("note", "improve", "block"))
_FEEDBACK_INVALIDATION_STAGES = frozenset(
    ("make", "playtest", "release", "deliver")
)


@dataclass(frozen=True)
class Feedback:
    """One actionable Playtest finding that sends the product back to Make."""

    code: str
    area: str
    severity: str
    finding: str
    change: str
    evidence_refs: Sequence[str] = field(default_factory=tuple)
    invalidates: Sequence[str] = ("playtest", "release", "deliver")

    def __post_init__(self) -> None:
        bounded_text(self.code, "feedback code", 200)
        bounded_text(self.area, "feedback area", 200)
        if self.severity not in _SEVERITIES:
            raise ContractError("feedback severity must be note, improve, or block")
        bounded_text(self.finding, "feedback finding")
        bounded_text(self.change, "feedback change")
        refs = tuple(self.evidence_refs)
        invalidates = tuple(self.invalidates)
        if any(not isinstance(item, str) or not item for item in refs):
            raise ContractError("feedback evidence_refs must be non-empty strings")
        if any(item not in _FEEDBACK_INVALIDATION_STAGES for item in invalidates):
            raise ContractError(
                "feedback invalidates a stage outside the Make repair loop"
            )
        object.__setattr__(self, "evidence_refs", refs)
        object.__setattr__(self, "invalidates", invalidates)

    def to_dict(self):
        return {
            "code": self.code,
            "area": self.area,
            "severity": self.severity,
            "finding": self.finding,
            "change": self.change,
            "evidence_refs": list(self.evidence_refs),
            "invalidates": list(self.invalidates),
        }


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


__all__ = ["Feedback", "Playtested"]
