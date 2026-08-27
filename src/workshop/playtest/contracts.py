"""Inputs and outputs owned by the Playtest stage."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from workshop._validation import bounded_text, require_sha256
from workshop.errors import ContractError
from workshop.playtest.service import Playtest


_SEVERITIES = frozenset(("note", "improve", "block"))
_ACTIVE_FEEDBACK_INVALIDATION_STAGES = frozenset(
    ("invent", "make", "playtest", "release")
)
# Read historical Make-feedback contracts that named the former executable
# Deliver wait boundary. New finalizers never author this marker.
_FEEDBACK_INVALIDATION_STAGES = _ACTIVE_FEEDBACK_INVALIDATION_STAGES | {"deliver"}
_CONCEPT_REVISION_INVALIDATIONS = _ACTIVE_FEEDBACK_INVALIDATION_STAGES


@dataclass(frozen=True)
class Feedback:
    """One authored Playtest finding with an explicit invalidation boundary."""

    code: str
    area: str
    severity: str
    finding: str
    change: str
    evidence_refs: Sequence[str] = field(default_factory=tuple)
    invalidates: Sequence[str] = ("playtest", "release")

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
                "feedback invalidates a stage outside the repair lifecycle"
            )
        if len(invalidates) != len(set(invalidates)):
            raise ContractError("feedback invalidates must not contain duplicates")
        if "invent" in invalidates:
            if self.severity not in ("improve", "block"):
                raise ContractError(
                    "only actionable feedback may request concept revision"
                )
            if set(invalidates) != _CONCEPT_REVISION_INVALIDATIONS:
                raise ContractError(
                    "concept revision must invalidate Invent and every downstream stage"
                )
        object.__setattr__(self, "evidence_refs", refs)
        object.__setattr__(self, "invalidates", invalidates)

    @property
    def requests_concept_revision(self) -> bool:
        """Return the agent-authored routing choice without judging its prose."""

        return (
            self.severity in ("improve", "block")
            and "invent" in self.invalidates
        )

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
