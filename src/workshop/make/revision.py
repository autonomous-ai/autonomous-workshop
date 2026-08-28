"""Evidence-bound request for Make to return an unbuildable concept to Invent.

Make does not revise the sealed Invent contract.  It may only identify the
exact upstream concept, preserve exact contradiction evidence, and ask the
host to spend one bounded lifecycle round on a new Invent Goal.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

from workshop._validation import (
    bounded_text,
    require_safe_evidence_path,
    require_sha256,
)
from workshop.artifacts import (
    ArtifactManifest,
    artifact_manifest_from_mapping,
    build_artifact_manifest,
)
from workshop.errors import ArtifactError, ContractError
from workshop.invent.native import NativeInvented
from workshop.match.native import NativeMatchAssignment


MAKE_INVENT_REVISION_CAPABILITY_PATH = (
    ".agents/skills/autonomous-workshop/references/make-invent-revision-v1.md"
)
MAKE_INVENT_REVISION_KIND = "autonomous-workshop.make-invent-revision"
MAKE_INVENT_REVISION_INVALIDATES = (
    "invent",
    "make",
    "playtest",
    "release",
)


def _canonical_json(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ContractError("Make Invent-revision values must be finite JSON") from exc


def _safe_relative(value: Any, label: str) -> PurePosixPath:
    try:
        validated = require_safe_evidence_path(value, label)
    except ContractError:
        raise
    return PurePosixPath(validated)


@dataclass(frozen=True)
class MakeInventRevisionFeedback:
    """One build-blocking contradiction in the exact sealed Invent concept."""

    code: str
    area: str
    severity: str
    finding: str
    change: str
    evidence_refs: Sequence[str]
    invalidates: Sequence[str] = MAKE_INVENT_REVISION_INVALIDATES

    def __post_init__(self) -> None:
        bounded_text(self.code, "Make Invent-revision feedback code", 200)
        bounded_text(self.area, "Make Invent-revision feedback area", 200)
        if self.severity != "block":
            raise ContractError(
                "Make may return to Invent only for build-blocking feedback"
            )
        bounded_text(self.finding, "Make Invent-revision feedback finding")
        bounded_text(self.change, "Make Invent-revision feedback change")
        refs = tuple(self.evidence_refs)
        if not refs:
            raise ContractError(
                "Make Invent-revision feedback requires exact evidence_refs"
            )
        for ref in refs:
            _safe_relative(ref, "Make Invent-revision feedback evidence_ref")
        if len(refs) != len(set(refs)):
            raise ContractError(
                "Make Invent-revision feedback evidence_refs must be unique"
            )
        invalidates = tuple(self.invalidates)
        if invalidates != MAKE_INVENT_REVISION_INVALIDATES:
            raise ContractError(
                "Make Invent revision must invalidate Invent and every downstream stage"
            )
        object.__setattr__(self, "evidence_refs", refs)
        object.__setattr__(self, "invalidates", invalidates)

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "area": self.area,
            "severity": self.severity,
            "finding": self.finding,
            "change": self.change,
            "evidence_refs": list(self.evidence_refs),
            "invalidates": list(self.invalidates),
        }

    @classmethod
    def from_mapping(cls, value: Any) -> "MakeInventRevisionFeedback":
        expected = {
            "code",
            "area",
            "severity",
            "finding",
            "change",
            "evidence_refs",
            "invalidates",
        }
        if not isinstance(value, Mapping) or set(value) != expected:
            raise ContractError("Make Invent-revision feedback fields are invalid")
        refs = value["evidence_refs"]
        invalidates = value["invalidates"]
        if isinstance(refs, (str, bytes)) or not isinstance(refs, Sequence):
            raise ContractError(
                "Make Invent-revision feedback evidence_refs must be an array"
            )
        if isinstance(invalidates, (str, bytes)) or not isinstance(
            invalidates, Sequence
        ):
            raise ContractError(
                "Make Invent-revision feedback invalidates must be an array"
            )
        return cls(
            code=value["code"],
            area=value["area"],
            severity=value["severity"],
            finding=value["finding"],
            change=value["change"],
            evidence_refs=tuple(refs),
            invalidates=tuple(invalidates),
        )


@dataclass(frozen=True)
class NativeMakeInventRevision:
    """One content-addressed request to replace an unbuildable Invent concept."""

    round: int
    wish_sha256: str
    assignment_sha256: str
    invented_sha256: str
    evidence_root: str
    evidence_manifest: ArtifactManifest
    feedback: Sequence[MakeInventRevisionFeedback]
    schema_version: int = 1
    kind: str = MAKE_INVENT_REVISION_KIND
    feedback_sha256: str = field(init=False)
    revision_request_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ContractError("Make Invent-revision schema_version must be 1")
        if self.kind != MAKE_INVENT_REVISION_KIND:
            raise ContractError("Make Invent-revision kind is invalid")
        if type(self.round) is not int or not 1 <= self.round <= 100:
            raise ContractError("Make Invent-revision round must be from 1 through 100")
        require_sha256(self.wish_sha256, "Make Invent-revision Wish sha256")
        require_sha256(
            self.assignment_sha256, "Make Invent-revision assignment sha256"
        )
        require_sha256(self.invented_sha256, "Make Invent-revision Invented sha256")
        expected_root = "artifacts/make/r%04d/revision-evidence" % self.round
        if _safe_relative(
            self.evidence_root, "Make Invent-revision evidence_root"
        ).as_posix() != expected_root:
            raise ContractError(
                "Make Invent-revision evidence_root is not canonical for its round"
            )
        if not isinstance(self.evidence_manifest, ArtifactManifest):
            raise ContractError("Make Invent revision requires an ArtifactManifest")
        self.evidence_manifest.assert_valid()
        feedback = tuple(self.feedback)
        if not feedback or not all(
            isinstance(item, MakeInventRevisionFeedback) for item in feedback
        ):
            raise ContractError("Make Invent revision requires typed feedback")
        if len({item.code for item in feedback}) != len(feedback):
            raise ContractError("Make Invent-revision feedback codes must be unique")
        inventory = {entry.path: entry.sha256 for entry in self.evidence_manifest.entries}
        for item in feedback:
            for ref in item.evidence_refs:
                if ref not in inventory:
                    raise ContractError(
                        "Make Invent-revision feedback references absent evidence: %s"
                        % ref
                    )
        object.__setattr__(self, "feedback", feedback)
        feedback_sha256 = hashlib.sha256(
            _canonical_json([item.to_dict() for item in feedback])
        ).hexdigest()
        object.__setattr__(self, "feedback_sha256", feedback_sha256)
        object.__setattr__(
            self,
            "revision_request_sha256",
            hashlib.sha256(_canonical_json(self._identity_dict())).hexdigest(),
        )

    def _identity_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "kind": self.kind,
            "round": self.round,
            "wish_sha256": self.wish_sha256,
            "assignment_sha256": self.assignment_sha256,
            "invented_sha256": self.invented_sha256,
            "evidence_root": self.evidence_root,
            "evidence_manifest": self.evidence_manifest.to_dict(),
            "feedback": [item.to_dict() for item in self.feedback],
            "feedback_sha256": self.feedback_sha256,
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self._identity_dict()
        payload["revision_request_sha256"] = self.revision_request_sha256
        return payload

    def assert_context(
        self,
        assignment: NativeMatchAssignment,
        invented: NativeInvented,
        *,
        expected_round: int,
    ) -> None:
        if not isinstance(assignment, NativeMatchAssignment) or not isinstance(
            invented, NativeInvented
        ):
            raise ContractError(
                "Make Invent-revision context requires assignment and Invented"
            )
        invented.assert_context(assignment)
        if (
            self.round != expected_round
            or self.wish_sha256 != assignment.wish_sha256
            or self.assignment_sha256 != assignment.assignment_sha256
            or self.invented_sha256 != invented.invented_sha256
        ):
            raise ContractError(
                "Make Invent-revision request belongs to different Workshop inputs"
            )

    def validate_evidence_tree(self, run_root: Path) -> ArtifactManifest:
        root = Path(run_root).resolve(strict=True)
        relative = _safe_relative(
            self.evidence_root, "Make Invent-revision evidence_root"
        )
        evidence_root = root.joinpath(*relative.parts)
        if evidence_root.is_symlink() or not evidence_root.is_dir():
            raise ArtifactError("Make Invent-revision evidence tree is unavailable")
        current = build_artifact_manifest(
            evidence_root, created_at=self.evidence_manifest.created_at
        )
        if current.to_dict() != self.evidence_manifest.to_dict():
            raise ArtifactError(
                "Make Invent-revision evidence differs from its manifest"
            )
        return current

    @classmethod
    def from_mapping(cls, value: Any) -> "NativeMakeInventRevision":
        expected = {
            "schema_version",
            "kind",
            "round",
            "wish_sha256",
            "assignment_sha256",
            "invented_sha256",
            "evidence_root",
            "evidence_manifest",
            "feedback",
            "feedback_sha256",
            "revision_request_sha256",
        }
        if not isinstance(value, Mapping) or set(value) != expected:
            raise ContractError("Make Invent-revision fields are invalid")
        feedback = value["feedback"]
        if isinstance(feedback, (str, bytes)) or not isinstance(feedback, Sequence):
            raise ContractError("Make Invent-revision feedback must be an array")
        request = cls(
            schema_version=value["schema_version"],
            kind=value["kind"],
            round=value["round"],
            wish_sha256=value["wish_sha256"],
            assignment_sha256=value["assignment_sha256"],
            invented_sha256=value["invented_sha256"],
            evidence_root=value["evidence_root"],
            evidence_manifest=artifact_manifest_from_mapping(
                value["evidence_manifest"]
            ),
            feedback=tuple(
                MakeInventRevisionFeedback.from_mapping(item) for item in feedback
            ),
        )
        if dict(value) != request.to_dict():
            raise ContractError(
                "Make Invent-revision hashes or canonical identity are invalid"
            )
        return request


__all__ = [
    "MAKE_INVENT_REVISION_CAPABILITY_PATH",
    "MAKE_INVENT_REVISION_INVALIDATES",
    "MAKE_INVENT_REVISION_KIND",
    "MakeInventRevisionFeedback",
    "NativeMakeInventRevision",
]
