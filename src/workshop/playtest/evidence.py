"""Immutable evidence records produced by the Playtest component."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Mapping

from workshop._validation import (
    require_exact_version,
    require_json_mapping,
    require_safe_evidence_path,
    require_sha256,
    require_utc_timestamp,
    utc_now,
)
from workshop.errors import ContractError


@dataclass(frozen=True)
class PlaytestResult:
    """One reproducible playtest verdict bound to exact artifact bytes.

    Workshop 0.3 persisted this contract with ``inspection_*`` field names.
    Those names intentionally remain stable on disk; ``playtest_id`` is the
    friendlier code-facing spelling for new inventors.
    """

    inspection_id: str
    passed: bool
    artifact_sha256: str
    evidence: Mapping[str, Any]
    evaluator: str
    evaluator_version: str
    config_sha256: str
    evidence_ref: str
    evidence_sha256: str
    observed_at: str

    @property
    def gate_id(self) -> str:
        """Compatibility spelling used by Workshop 0.2 and older."""

        return self.inspection_id

    @property
    def playtest_id(self) -> str:
        """Canonical spelling for the persisted ``inspection_id`` field."""

        return self.inspection_id

    def __post_init__(self) -> None:
        self.assert_valid()

    def assert_valid(self) -> None:
        if not self.inspection_id or not isinstance(self.inspection_id, str):
            raise ContractError("inspection_id must be a non-empty string")
        if not isinstance(self.passed, bool):
            raise ContractError("inspection passed must be boolean")
        require_sha256(self.artifact_sha256, "inspection artifact_sha256")
        if (
            not isinstance(self.evaluator, str)
            or not self.evaluator
            or self.evaluator.casefold() in {"self-report", "trust-me"}
        ):
            raise ContractError("inspection evaluator must be named")
        require_exact_version(self.evaluator_version, "inspection evaluator_version")
        require_sha256(self.config_sha256, "gate config_sha256")
        require_safe_evidence_path(self.evidence_ref, "inspection evidence_ref")
        require_sha256(self.evidence_sha256, "inspection evidence_sha256")
        require_utc_timestamp(self.observed_at, "inspection observed_at")
        if not self.evidence:
            raise ContractError("inspection evidence must be a non-empty object")
        require_json_mapping(self.evidence, "inspection evidence")

    @classmethod
    def create(
        cls,
        inspection_id: str,
        passed: bool,
        artifact_sha256: str,
        evidence: Mapping[str, Any],
        evaluator: str,
        evaluator_version: str,
        config_sha256: str,
        evidence_ref: str,
        evidence_sha256: str,
    ) -> "PlaytestResult":
        return cls(
            inspection_id,
            passed,
            artifact_sha256,
            evidence,
            evaluator,
            evaluator_version,
            config_sha256,
            evidence_ref,
            evidence_sha256,
            utc_now(),
        )

    def to_dict(self) -> Dict[str, Any]:
        self.assert_valid()
        return asdict(self)


# Persisted and pre-0.4 vocabulary remains type-identical, not wrapped.
InspectionResult = PlaytestResult
GateResult = PlaytestResult


__all__ = ["GateResult", "InspectionResult", "PlaytestResult"]
