"""Playtest evidence that stays bound to the exact toy or game it tested."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Sequence

from workshop.artifacts.core import ArtifactManifest
from workshop.errors import ContractError
from workshop.playtest.evidence import PlaytestResult


@dataclass(frozen=True)
class Playtest:
    """A complete, artifact-bound playtest report for one Make.

    Product files stay bound to ``artifact_manifest``. Playtest evidence files
    may be sealed separately in ``evidence_manifest`` so AI-player feedback can
    improve the next Make without changing the exact product bytes that were
    tested. Failed results remain useful feedback; the native stage contract
    and host gate own approval.

    """

    artifact_manifest: ArtifactManifest
    results: Sequence[PlaytestResult]
    evidence_manifest: ArtifactManifest

    def __post_init__(self) -> None:
        object.__setattr__(self, "results", tuple(self.results))
        self.assert_valid()

    @property
    def artifact_sha256(self) -> str:
        return self.artifact_manifest.artifact_sha256

    @property
    def evidence_artifact_sha256(self) -> str:
        return self.evidence_manifest.artifact_sha256

    @property
    def passed(self) -> bool:
        return bool(self.results) and all(result.passed for result in self.results)

    def assert_valid(self) -> None:
        if not isinstance(self.artifact_manifest, ArtifactManifest):
            raise ContractError("Playtest requires an ArtifactManifest")
        self.artifact_manifest.assert_valid()
        if not isinstance(self.evidence_manifest, ArtifactManifest):
            raise ContractError("Playtest requires an evidence ArtifactManifest")
        self.evidence_manifest.assert_valid()
        if not self.results:
            raise ContractError("Playtest requires at least one PlaytestResult")
        evidence_inventory = {
            entry.path: entry.sha256 for entry in self.evidence_manifest.entries
        }
        seen = set()
        for result in self.results:
            if not isinstance(result, PlaytestResult):
                raise ContractError(
                    "Playtest results must use the PlaytestResult contract"
                )
            result.assert_valid()
            if result.playtest_id in seen:
                raise ContractError(
                    "duplicate PlaytestResult %r" % result.playtest_id
                )
            seen.add(result.playtest_id)
            if result.artifact_sha256 != self.artifact_sha256:
                raise ContractError(
                    "PlaytestResult %s belongs to different artifact bytes"
                    % result.playtest_id
                )
            if evidence_inventory.get(result.evidence_ref) != result.evidence_sha256:
                raise ContractError(
                    "PlaytestResult %s evidence is absent or hash-mismatched "
                    "in the sealed evidence artifact" % result.playtest_id
                )

    def to_dict(self) -> Dict[str, Any]:
        self.assert_valid()
        return {
            "schema_version": 1,
            "artifact_sha256": self.artifact_sha256,
            "evidence_artifact_sha256": self.evidence_artifact_sha256,
            "passed": self.passed,
            "results": [result.to_dict() for result in self.results],
        }
