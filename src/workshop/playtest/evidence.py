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
)
from workshop.errors import ContractError


@dataclass(frozen=True)
class PlaytestResult:
    """One reproducible Playtest verdict bound to exact artifact bytes."""

    playtest_id: str
    passed: bool
    artifact_sha256: str
    evidence: Mapping[str, Any]
    evaluator: str
    evaluator_version: str
    config_sha256: str
    evidence_ref: str
    evidence_sha256: str
    observed_at: str

    def __post_init__(self) -> None:
        self.assert_valid()

    def assert_valid(self) -> None:
        if not isinstance(self.playtest_id, str) or not self.playtest_id:
            raise ContractError("playtest_id must be a non-empty string")
        if not isinstance(self.passed, bool):
            raise ContractError("PlaytestResult passed must be boolean")
        require_sha256(self.artifact_sha256, "PlaytestResult artifact_sha256")
        if (
            not isinstance(self.evaluator, str)
            or not self.evaluator
            or self.evaluator.casefold() in {"self-report", "trust-me"}
        ):
            raise ContractError("PlaytestResult evaluator must be named")
        require_exact_version(self.evaluator_version, "PlaytestResult evaluator_version")
        require_sha256(self.config_sha256, "PlaytestResult config_sha256")
        require_safe_evidence_path(self.evidence_ref, "PlaytestResult evidence_ref")
        require_sha256(self.evidence_sha256, "PlaytestResult evidence_sha256")
        require_utc_timestamp(self.observed_at, "PlaytestResult observed_at")
        if not self.evidence:
            raise ContractError("PlaytestResult evidence must be a non-empty object")
        require_json_mapping(self.evidence, "PlaytestResult evidence")

    def to_dict(self) -> Dict[str, Any]:
        self.assert_valid()
        return asdict(self)

__all__ = ["PlaytestResult"]
