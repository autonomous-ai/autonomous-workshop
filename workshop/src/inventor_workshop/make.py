"""Typed, fail-closed composition for concept-to-verified-CAD creation."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

from .artifacts import ArtifactManifest, build_artifact_manifest
from .cad import CadReleaseBundle
from .errors import ArtifactError, ContractError
from .doors import CadDoor, CadInspectionDoor, InspectionDoor, ModelDoor
from .inspection import Inspection
from .models import InspectionResult, require_json_mapping, require_sha256
from .taste import Taste, load_taste


MAX_PRODUCT_ID_CHARS = 256
MAX_OBJECTIVE_CHARS = 50_000
_UNSET = object()


def _bounded_text(
    value: str, label: str, maximum: int, allow_format_controls: bool = False
) -> str:
    permitted_controls = "\n\r\t" if allow_format_controls else ""
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value) > maximum
        or any(
            ord(character) < 32 and character not in permitted_controls
            for character in value
        )
        or any(ord(character) == 127 for character in value)
    ):
        raise ContractError("%s must be bounded, non-empty, and control-free" % label)
    return value


def _copy_mapping(value: Mapping[str, Any], label: str, nonempty: bool = False) -> Dict[str, Any]:
    require_json_mapping(value, label)
    if nonempty and not value:
        raise ContractError("%s must be a non-empty object" % label)
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    copied = json.loads(payload)
    if not isinstance(copied, dict):
        raise ContractError("%s must be an object" % label)
    return copied


def _mapping_sha256(value: Mapping[str, Any], label: str) -> str:
    copied = _copy_mapping(value, label, nonempty=True)
    payload = json.dumps(
        copied,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class Wish:
    schema_version: int
    product_id: str
    objective: str
    constraints: Mapping[str, Any] = field(default_factory=dict)
    context: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "constraints", _copy_mapping(self.constraints, "wish constraints")
        )
        object.__setattr__(self, "context", _copy_mapping(self.context, "wish context"))
        self.assert_valid()

    def assert_valid(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ContractError("wish schema_version must be 1")
        _bounded_text(self.product_id, "wish product_id", MAX_PRODUCT_ID_CHARS)
        if any(character in "/\\" for character in self.product_id):
            raise ContractError("wish product_id must not contain path separators")
        _bounded_text(
            self.objective,
            "wish objective",
            MAX_OBJECTIVE_CHARS,
            allow_format_controls=True,
        )
        _copy_mapping(self.constraints, "wish constraints")
        _copy_mapping(self.context, "wish context")

    @classmethod
    def create(
        cls,
        product_id: str,
        objective: str,
        constraints: Optional[Mapping[str, Any]] = None,
        context: Optional[Mapping[str, Any]] = None,
    ) -> "Wish":
        return cls(
            1,
            product_id,
            objective,
            constraints if constraints is not None else {},
            context if context is not None else {},
        )

    def to_dict(self) -> Dict[str, Any]:
        self.assert_valid()
        return {
            "schema_version": self.schema_version,
            "product_id": self.product_id,
            "objective": self.objective,
            "constraints": _copy_mapping(self.constraints, "wish constraints"),
            "context": _copy_mapping(self.context, "wish context"),
        }


@dataclass(frozen=True)
class CadBuildResult:
    schema_version: int
    product_id: str
    artifact_root: Path
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        requested_root = Path(self.artifact_root)
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ContractError("CAD build result schema_version must be 1")
        _bounded_text(self.product_id, "CAD build product_id", MAX_PRODUCT_ID_CHARS)
        if not requested_root.is_absolute():
            raise ContractError("CAD build artifact_root must be absolute")
        if requested_root.is_symlink():
            raise ContractError("CAD build artifact_root must be a regular directory")
        try:
            resolved_root = requested_root.resolve(strict=True)
        except OSError as exc:
            raise ContractError("cannot resolve CAD build artifact_root") from exc
        if not resolved_root.is_dir():
            raise ContractError("CAD build artifact_root must be a regular directory")
        object.__setattr__(self, "artifact_root", resolved_root)
        object.__setattr__(self, "metadata", _copy_mapping(self.metadata, "CAD build metadata"))

    def assert_valid(self) -> None:
        self.__post_init__()

    def to_dict(self) -> Dict[str, Any]:
        self.assert_valid()
        return {
            "schema_version": self.schema_version,
            "product_id": self.product_id,
            "artifact_root": str(self.artifact_root),
            "metadata": _copy_mapping(self.metadata, "CAD build metadata"),
        }


@dataclass(frozen=True, init=False)
class MakeResult:
    schema_version: int
    wish: Wish
    taste: Taste
    concept: Mapping[str, Any]
    concept_sha256: str
    cad_build: CadBuildResult
    artifact_manifest: ArtifactManifest
    cad_release: Optional[CadReleaseBundle]
    inspections: Sequence[InspectionResult]

    def __init__(
        self,
        schema_version: int,
        wish: Any = _UNSET,
        taste: Any = _UNSET,
        concept: Any = _UNSET,
        concept_sha256: Any = _UNSET,
        cad_build: Any = _UNSET,
        artifact_manifest: Any = _UNSET,
        cad_release: Any = _UNSET,
        inspections: Any = _UNSET,
        *,
        brief: Any = _UNSET,
        gates: Any = _UNSET,
    ) -> None:
        """Build a canonical result while reading Workshop 0.2 field names.

        Positional construction keeps the v0.2 field order. Keyword callers
        should use ``wish`` and ``inspections``; ``brief`` and ``gates`` are
        accepted only as compatibility inputs and are never emitted.
        """

        if wish is _UNSET:
            wish = brief
        elif brief is not _UNSET and wish != brief:
            raise ContractError("make result has conflicting wish and brief")
        if inspections is _UNSET:
            inspections = () if gates is _UNSET else gates
        elif gates is not _UNSET:
            try:
                aliases_match = tuple(inspections) == tuple(gates)
            except TypeError as exc:
                raise ContractError(
                    "make result has invalid inspections or gates"
                ) from exc
            if not aliases_match:
                raise ContractError(
                    "make result has conflicting inspections and gates"
                )
        if cad_release is _UNSET:
            cad_release = None
        for name, value in (
            ("schema_version", schema_version),
            ("wish", wish),
            ("taste", taste),
            ("concept", concept),
            ("concept_sha256", concept_sha256),
            ("cad_build", cad_build),
            ("artifact_manifest", artifact_manifest),
            ("cad_release", cad_release),
            ("inspections", inspections),
        ):
            object.__setattr__(self, name, value)
        self.__post_init__()

    @property
    def brief(self) -> Wish:
        """Compatibility spelling used by Workshop 0.2 and older."""

        return self.wish

    @property
    def gates(self) -> Sequence[InspectionResult]:
        """Compatibility spelling used by Workshop 0.2 and older."""

        return self.inspections

    def __post_init__(self) -> None:
        object.__setattr__(self, "concept", _copy_mapping(self.concept, "make concept", True))
        if isinstance(self.inspections, (str, bytes, Mapping)):
            raise ContractError("make result requires typed inspections")
        try:
            inspections = tuple(self.inspections)
        except TypeError as exc:
            raise ContractError("make result requires typed inspections") from exc
        object.__setattr__(self, "inspections", inspections)
        self.assert_valid()

    def assert_valid(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ContractError("make result schema_version must be 1")
        if not isinstance(self.wish, Wish):
            raise ContractError("make result requires a typed Wish")
        self.wish.assert_valid()
        if not isinstance(self.taste, Taste):
            raise ContractError("make result requires a typed Taste")
        self.taste.assert_valid()
        concept = _copy_mapping(self.concept, "make concept", True)
        require_sha256(self.concept_sha256, "make concept sha256")
        if _mapping_sha256(concept, "make concept") != self.concept_sha256:
            raise ContractError("make concept identity is inconsistent")
        if not isinstance(self.cad_build, CadBuildResult):
            raise ContractError("make result requires a typed CAD build")
        self.cad_build.assert_valid()
        if self.cad_build.product_id != self.wish.product_id:
            raise ContractError("CAD build belongs to a different product")
        if not isinstance(self.artifact_manifest, ArtifactManifest):
            raise ContractError("make result requires a typed artifact manifest")
        self.artifact_manifest.assert_valid()
        artifact_entries = {
            entry.path: entry.sha256 for entry in self.artifact_manifest.entries
        }
        if self.cad_release is not None:
            if not isinstance(self.cad_release, CadReleaseBundle):
                raise ContractError("make result CAD release must use CadReleaseBundle")
            self.cad_release.assert_artifact(
                self.artifact_manifest.artifact_sha256
            )
            for path, digest in self.cad_release.manifest.evidence_files.items():
                if artifact_entries.get(path) != digest:
                    raise ContractError(
                        "CAD evidence is absent or hash-mismatched in the sealed artifact: %s"
                        % path
                    )
            for part in self.cad_release.manifest.parts:
                for path in (part.source_path, part.step_path, part.stl_path):
                    if path not in artifact_entries:
                        raise ContractError(
                            "CAD part file is absent from the sealed artifact: %s" % path
                        )

        if not all(
            isinstance(inspection, InspectionResult)
            for inspection in self.inspections
        ):
            raise ContractError("make result requires typed inspections")
        inspection_ids = [result.inspection_id for result in self.inspections]
        if len(inspection_ids) != len(set(inspection_ids)):
            raise ContractError("make inspector returned duplicate inspection ids")
        for result in self.inspections:
            result.assert_valid()
            if not result.passed:
                raise ContractError(
                    "InspectionResult %s did not pass" % result.inspection_id
                )
            if result.artifact_sha256 != self.artifact_manifest.artifact_sha256:
                raise ContractError(
                    "InspectionResult %s belongs to different artifact bytes"
                    % result.inspection_id
                )
            if artifact_entries.get(result.evidence_ref) != result.evidence_sha256:
                raise ContractError(
                    "InspectionResult %s evidence is absent or hash-mismatched in the sealed artifact"
                    % result.inspection_id
                )
            if result.inspection_id == "cad" and (
                self.cad_release is None
                or result.evidence.get("cad_release_sha256") != self.cad_release.sha256
                or result.evidence_sha256 != self.cad_release.sha256
            ):
                raise ContractError(
                    "CAD inspection does not bind the validated release bundle"
                )

    def to_dict(self) -> Dict[str, Any]:
        self.assert_valid()
        return {
            "schema_version": self.schema_version,
            "wish": self.wish.to_dict(),
            "taste": self.taste.to_binding(),
            "concept": _copy_mapping(self.concept, "make concept", True),
            "concept_sha256": self.concept_sha256,
            "cad_build": self.cad_build.to_dict(),
            "artifact_manifest": self.artifact_manifest.to_dict(),
            "cad_release_sha256": (
                self.cad_release.sha256 if self.cad_release is not None else None
            ),
            "inspections": [result.to_dict() for result in self.inspections],
        }


class Workbench:
    """Make one Wish, then inspect its exact artifact bytes explicitly."""

    def __init__(
        self,
        agent: ModelDoor,
        cad: CadDoor,
        verifier: CadInspectionDoor,
        evaluator: Optional[InspectionDoor] = None,
        concept_role: str = "concept",
    ) -> None:
        _bounded_text(concept_role, "make concept role", 128)
        for adapter, method, label in (
            (agent, "run", "agent"),
            (cad, "build", "CAD"),
            (verifier, "verify", "CAD verifier"),
        ):
            if not callable(getattr(adapter, method, None)):
                raise ContractError("%s adapter must implement %s()" % (label, method))
        self.agent = agent
        self.cad = cad
        self.verifier = verifier
        if evaluator is None:
            self._inspect = None
        elif callable(getattr(evaluator, "inspect", None)):
            self._inspect = evaluator.inspect
        elif callable(getattr(evaluator, "evaluate", None)):
            self._inspect = evaluator.evaluate
        else:
            raise ContractError("inspector adapter must implement inspect()")
        self.inspector = evaluator
        self.evaluator = evaluator  # compatibility attribute
        self.concept_role = concept_role

    def make(
        self,
        wish: Any = _UNSET,
        inventor_root: Any = _UNSET,
        workspace: Any = _UNSET,
        budget_micros: Any = _UNSET,
        *,
        brief: Any = _UNSET,
    ) -> MakeResult:
        if wish is _UNSET:
            wish = brief
        elif brief is not _UNSET and wish != brief:
            raise ContractError("Workbench.make has conflicting wish and brief")
        if not isinstance(wish, Wish):
            raise ContractError("Workbench requires a typed Wish")
        wish.assert_valid()
        if (
            type(budget_micros) is not int
            or budget_micros <= 0
        ):
            raise ContractError("make budget_micros must be a positive integer")
        taste = load_taste(inventor_root)
        run_root = self._prepare_workspace(workspace)
        request = {
            "schema_version": 1,
            "wish": wish.to_dict(),
            "taste": taste.to_binding(),
        }
        raw_concept = self.agent.run(self.concept_role, request, budget_micros)
        concept = _copy_mapping(raw_concept, "agent concept", nonempty=True)
        concept_sha256 = _mapping_sha256(concept, "agent concept")
        taste.assert_current()

        cad_build = self.cad.build(wish, concept, run_root)
        if not isinstance(cad_build, CadBuildResult):
            raise ContractError("CAD adapter must return CadBuildResult")
        cad_build.assert_valid()
        if cad_build.product_id != wish.product_id:
            raise ContractError("CAD adapter returned a different product id")
        artifact_root = cad_build.artifact_root.resolve(strict=True)
        try:
            artifact_root.relative_to(run_root)
        except ValueError as exc:
            raise ArtifactError(
                "CAD artifact root must stay inside the make workspace"
            ) from exc

        manifest = build_artifact_manifest(artifact_root, created_at="content-addressed")
        taste.assert_current()
        return MakeResult(
            schema_version=1,
            wish=wish,
            taste=taste,
            concept=concept,
            concept_sha256=concept_sha256,
            cad_build=cad_build,
            artifact_manifest=manifest,
            cad_release=None,
            inspections=(),
        )

    def inspect(self, made: MakeResult) -> Inspection:
        """Run the configured inspector against one completed MakeResult."""

        if not isinstance(made, MakeResult):
            raise ContractError("Workbench.inspect requires a MakeResult")
        made.assert_valid()
        if made.inspections:
            raise ContractError(
                "Workbench.inspect requires an uninspected MakeResult"
            )
        if self._inspect is None:
            raise ContractError("Workbench has no InspectionDoor")
        artifact_root = made.cad_build.artifact_root
        before = build_artifact_manifest(
            artifact_root, created_at="content-addressed"
        )
        if before.to_dict() != made.artifact_manifest.to_dict():
            raise ArtifactError("artifact changed after Make")
        cad_release = self.verifier.verify(
            artifact_root, made.artifact_manifest.artifact_sha256
        )
        if not isinstance(cad_release, CadReleaseBundle):
            raise ContractError("CAD Inspection Door must return CadReleaseBundle")
        cad_release.assert_artifact(made.artifact_manifest.artifact_sha256)
        raw_results = self._inspect(
            artifact_root, made.artifact_manifest.artifact_sha256
        )
        if (
            isinstance(raw_results, (str, bytes, Mapping))
            or not isinstance(raw_results, Sequence)
        ):
            raise ContractError(
                "inspector must return a sequence of InspectionResult objects"
            )
        results: Tuple[InspectionResult, ...] = tuple(raw_results)
        after = build_artifact_manifest(
            artifact_root, created_at="content-addressed"
        )
        if after.to_dict() != made.artifact_manifest.to_dict():
            raise ArtifactError("artifact changed during Inspect")
        made.taste.assert_current()
        return Inspection(made.artifact_manifest, results, cad_release)

    def create(
        self,
        brief: Wish,
        inventor_root: Path,
        workspace: Path,
        budget_micros: int,
    ) -> MakeResult:
        """Compatibility path that combines canonical Make and Inspect."""

        made = self.make(brief, inventor_root, workspace, budget_micros)
        inspection = self.inspect(made)
        return MakeResult(
            schema_version=made.schema_version,
            wish=made.wish,
            taste=made.taste,
            concept=made.concept,
            concept_sha256=made.concept_sha256,
            cad_build=made.cad_build,
            artifact_manifest=made.artifact_manifest,
            cad_release=inspection.cad_release,
            inspections=inspection.results,
        )

    @staticmethod
    def _prepare_workspace(workspace: Path) -> Path:
        requested = Path(workspace)
        if requested.is_symlink():
            raise ArtifactError("make workspace must not be a symlink")
        if requested.exists():
            if not requested.is_dir():
                raise ArtifactError("make workspace must be a directory")
            if any(requested.iterdir()):
                raise ArtifactError("make workspace must be fresh and empty")
        else:
            requested.mkdir(parents=True, mode=0o700)
        return requested.resolve(strict=True)


# Compatibility names used before Workshop 0.3. New code uses the names on the
# left side of the customer/developer story: Wish and Workbench.make().
CreationBrief = Wish
CreationResult = MakeResult
Forge = Workbench
ProductForge = Workbench
