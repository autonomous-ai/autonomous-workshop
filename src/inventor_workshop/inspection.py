"""Inspection evidence that stays bound to the exact artifact it checked."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional, Sequence, Tuple

from .artifacts import ArtifactManifest
from .cad import CadReleaseBundle
from .errors import ContractError, TransitionError
from .models import InspectionResult


@dataclass(frozen=True)
class Inspection:
    """A complete, artifact-bound inspection report for one Make.

    Product files stay bound to ``artifact_manifest``. Inspection and review
    files may be sealed separately in ``evidence_manifest`` so the exact
    product-only bytes can become a Pack without discarding the evidence that
    approved them. Omitting ``evidence_manifest`` preserves the original
    single-manifest contract. Failed checks remain valid feedback that an
    inventor can learn from; :meth:`require` is the approval boundary and
    refuses to advance a Workflow until every required check passed.
    """

    artifact_manifest: ArtifactManifest
    results: Sequence[InspectionResult]
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
            raise ContractError("Inspection requires an ArtifactManifest")
        self.artifact_manifest.assert_valid()
        if not isinstance(self.evidence_manifest, ArtifactManifest):
            raise ContractError("Inspection requires an evidence ArtifactManifest")
        self.evidence_manifest.assert_valid()
        if not self.results:
            raise ContractError("Inspection requires at least one InspectionResult")
        product_inventory = {
            entry.path: entry.sha256 for entry in self.artifact_manifest.entries
        }
        evidence_inventory = {
            entry.path: entry.sha256 for entry in self.evidence_manifest.entries
        }
        if self.cad_release is not None:
            if not isinstance(self.cad_release, CadReleaseBundle):
                raise ContractError("Inspection CAD release must use CadReleaseBundle")
            self.cad_release.assert_artifact(self.artifact_sha256)
            for path, digest in self.cad_release.manifest.evidence_files.items():
                if evidence_inventory.get(path) != digest:
                    raise ContractError(
                        "CAD evidence is absent or hash-mismatched in the sealed "
                        "evidence artifact: %s"
                        % path
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
            if not isinstance(result, InspectionResult):
                raise ContractError(
                    "Inspection results must use the InspectionResult contract"
                )
            result.assert_valid()
            if result.inspection_id in seen:
                raise ContractError(
                    "duplicate InspectionResult %r" % result.inspection_id
                )
            seen.add(result.inspection_id)
            if result.artifact_sha256 != self.artifact_sha256:
                raise ContractError(
                    "InspectionResult %s belongs to different artifact bytes"
                    % result.inspection_id
                )
            if evidence_inventory.get(result.evidence_ref) != result.evidence_sha256:
                raise ContractError(
                    "InspectionResult %s evidence is absent or hash-mismatched "
                    "in the sealed evidence artifact" % result.inspection_id
                )

    def require(self, inspection_ids: Iterable[str]) -> Tuple[InspectionResult, ...]:
        """Return requested results in stable order or fail closed."""

        self.assert_valid()
        required = set(inspection_ids)
        by_id = {result.inspection_id: result for result in self.results}
        missing = required - set(by_id)
        if missing:
            raise TransitionError(
                "Inspection lacks required results: %s" % sorted(missing)
            )
        failed = sorted(name for name in required if not by_id[name].passed)
        if failed:
            raise TransitionError(
                "Inspection did not pass required results: %s" % failed
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
