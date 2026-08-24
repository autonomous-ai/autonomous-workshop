"""Playtest evidence that stays bound to the exact toy or game it tested."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional, Sequence, Tuple

from .artifacts import ArtifactManifest
from .cad import CadReleaseBundle
from .errors import ContractError, TransitionError
from .models import PlaytestResult


@dataclass(frozen=True)
class Playtest:
    """A complete, artifact-bound playtest report for one Make.

    Product files stay bound to ``artifact_manifest``. Playtest and review
    files may be sealed separately in ``evidence_manifest`` so feedback can
    improve the next Make without changing the exact product bytes that were
    tested. Failed results are useful feedback; :meth:`require` is the
    approval boundary and refuses to finish until every required check passes.

    Persisted result fields retain their Workshop 0.3 ``inspection_*`` names
    so old runs remain readable.
    """

    artifact_manifest: ArtifactManifest
    results: Sequence[PlaytestResult]
    cad_release: Optional[CadReleaseBundle] = None
    evidence_manifest: Optional[ArtifactManifest] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "results", tuple(self.results))
        if self.evidence_manifest is None:
            object.__setattr__(self, "evidence_manifest", self.artifact_manifest)
        self.assert_valid()

    @property
    def artifact_sha256(self) -> str:
        return self.artifact_manifest.artifact_sha256

    @property
    def evidence_artifact_sha256(self) -> str:
        # ``__post_init__`` turns the compatibility default into an explicit
        # manifest before validation.
        return self.evidence_manifest.artifact_sha256  # type: ignore[union-attr]

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
        product_inventory = {
            entry.path: entry.sha256 for entry in self.artifact_manifest.entries
        }
        evidence_inventory = {
            entry.path: entry.sha256 for entry in self.evidence_manifest.entries
        }
        if self.cad_release is not None:
            if not isinstance(self.cad_release, CadReleaseBundle):
                raise ContractError("Playtest CAD release must use CadReleaseBundle")
            self.cad_release.assert_artifact(self.artifact_sha256)
            for path, digest in self.cad_release.manifest.evidence_files.items():
                if evidence_inventory.get(path) != digest:
                    raise ContractError(
                        "CAD evidence is absent or hash-mismatched in the sealed "
                        "evidence artifact: %s" % path
                    )
            for part in self.cad_release.manifest.parts:
                for path in (part.source_path, part.step_path, part.stl_path):
                    if path not in product_inventory:
                        raise ContractError(
                            "CAD part file is absent from the sealed product artifact: %s"
                            % path
                        )
        seen = set()
        for result in self.results:
            if not isinstance(result, PlaytestResult):
                raise ContractError(
                    "Playtest results must use the PlaytestResult contract"
                )
            result.assert_valid()
            if result.inspection_id in seen:
                raise ContractError(
                    "duplicate PlaytestResult %r" % result.inspection_id
                )
            seen.add(result.inspection_id)
            if result.artifact_sha256 != self.artifact_sha256:
                raise ContractError(
                    "PlaytestResult %s belongs to different artifact bytes"
                    % result.inspection_id
                )
            if evidence_inventory.get(result.evidence_ref) != result.evidence_sha256:
                raise ContractError(
                    "PlaytestResult %s evidence is absent or hash-mismatched "
                    "in the sealed evidence artifact" % result.inspection_id
                )

    def require(self, playtest_ids: Iterable[str]) -> Tuple[PlaytestResult, ...]:
        """Return requested results in stable order or fail closed."""

        self.assert_valid()
        required = set(playtest_ids)
        by_id = {result.inspection_id: result for result in self.results}
        missing = required - set(by_id)
        if missing:
            raise TransitionError(
                "Playtest lacks required results: %s" % sorted(missing)
            )
        failed = sorted(name for name in required if not by_id[name].passed)
        if failed:
            raise TransitionError(
                "Playtest did not pass required results: %s" % failed
            )
        return tuple(by_id[name] for name in sorted(required))

    def to_dict(self) -> Dict[str, Any]:
        self.assert_valid()
        return {
            "schema_version": 1,
            "artifact_sha256": self.artifact_sha256,
            "evidence_artifact_sha256": self.evidence_artifact_sha256,
            "passed": self.passed,
            "cad_release_sha256": (
                self.cad_release.sha256 if self.cad_release is not None else None
            ),
            "results": [result.to_dict() for result in self.results],
        }

