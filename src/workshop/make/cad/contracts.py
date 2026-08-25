"""Canonical CAD inventory and fail-closed verification receipts."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from pathlib import PurePosixPath
from types import MappingProxyType
from typing import Any, Dict, Mapping, Optional, Sequence

from workshop.errors import ContractError, TransitionError
from workshop._validation import (
    require_exact_version,
    require_json_mapping,
    require_sha256,
    require_utc_timestamp,
    utc_now,
)

RESULTS = frozenset(("passed", "failed", "held"))
PROVENANCE = frozenset(("observed", "derived", "assumed"))
WORKSHOP_REQUIRED_CHECKS = frozenset(
    (
        "manifest",
        "brep",
        "mesh-topology",
        "dimensions",
        "interference",
        "bed-packing",
        "slicer",
        "form-review",
        "safety",
    )
)
WORKSHOP_CHECK_SUBSTRATES = MappingProxyType({
    "manifest": "deterministic",
    "brep": "deterministic",
    "mesh-topology": "deterministic",
    "dimensions": "deterministic",
    "interference": "deterministic",
    "bed-packing": "deterministic",
    "slicer": "deterministic",
    "form-review": "independent-review",
    "safety": "independent-review",
    "physical-claims": "physical",
})
WORKSHOP_CHECKS = frozenset(WORKSHOP_CHECK_SUBSTRATES)

# These are deliberately small, engine-neutral release floors. Validators may
# emit additional project-specific measurements, but a Workshop check cannot pass
# on an arbitrary truthy value such as {"checked": true}. ``minimum`` is a
# domain constraint for every supplied value; ``pass_*`` constraints apply to
# passed checks and are the minimum acceptance semantics shared by inventors.
_WORKSHOP_CHECK_MEASUREMENTS = {
    "manifest": {
        "inventory_valid": {"type": "boolean", "pass_value": True},
    },
    "brep": {
        "valid_solids": {"type": "integer", "minimum": 0, "pass_minimum": 1},
        "invalid_solids": {"type": "integer", "minimum": 0, "pass_maximum": 0},
    },
    "mesh-topology": {
        "watertight_parts": {"type": "integer", "minimum": 0, "pass_minimum": 1},
        "non_manifold_edges": {"type": "integer", "minimum": 0, "pass_maximum": 0},
    },
    "dimensions": {
        "measured_parts": {"type": "integer", "minimum": 0, "pass_minimum": 1},
        "out_of_tolerance": {"type": "integer", "minimum": 0, "pass_maximum": 0},
    },
    "interference": {
        "poses_tested": {"type": "integer", "minimum": 0, "pass_minimum": 1},
        "forbidden_intersections": {
            "type": "integer",
            "minimum": 0,
            "pass_maximum": 0,
        },
    },
    "bed-packing": {
        "beds_used": {"type": "integer", "minimum": 0, "pass_minimum": 1},
        "out_of_bounds_parts": {"type": "integer", "minimum": 0, "pass_maximum": 0},
    },
    "slicer": {
        "profiles_checked": {"type": "integer", "minimum": 0, "pass_minimum": 1},
        "slicer_errors": {"type": "integer", "minimum": 0, "pass_maximum": 0},
        "support_material_grams": {"type": "number", "minimum": 0},
    },
    "form-review": {
        "views_reviewed": {"type": "integer", "minimum": 0, "pass_minimum": 3},
        "blockers": {"type": "integer", "minimum": 0, "pass_maximum": 0},
    },
    "safety": {
        "hazards_found": {"type": "integer", "minimum": 0, "pass_maximum": 0},
        "review_scope": {"type": "string", "min_length": 1},
    },
    "physical-claims": {
        "claims_tested": {"type": "integer", "minimum": 0, "pass_minimum": 1},
        "claims_failed": {"type": "integer", "minimum": 0, "pass_maximum": 0},
    },
}
WORKSHOP_CHECK_MEASUREMENTS = MappingProxyType(
    {
        check_id: MappingProxyType(
            {
                name: MappingProxyType(dict(rule))
                for name, rule in measurements.items()
            }
        )
        for check_id, measurements in _WORKSHOP_CHECK_MEASUREMENTS.items()
    }
)
SUBSTRATES = frozenset(WORKSHOP_CHECK_SUBSTRATES.values())
ZERO_SHA256 = "0" * 64


def _plain_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _plain_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain_json(item) for item in value]
    return value


def _path(value: str, label: str) -> str:
    candidate = PurePosixPath(value) if isinstance(value, str) else PurePosixPath(".")
    if (
        not isinstance(value, str)
        or not value
        or not candidate.parts
        or value in (".", "..")
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
        or "\\" in value
        or candidate.is_absolute()
        or ".." in candidate.parts
        or candidate.as_posix() != value
    ):
        raise ContractError("%s must be a safe relative POSIX path" % label)
    return value


def _validate_workshop_measurements(
    check_id: str, status: str, measurements: Mapping[str, Any]
) -> None:
    """Validate typed Workshop metrics and the release floor for passed checks."""
    if not all(isinstance(name, str) and name for name in measurements):
        raise ContractError("verification measurement names must be non-empty strings")
    rules = WORKSHOP_CHECK_MEASUREMENTS.get(check_id)
    if rules is None:
        return
    for name, rule in rules.items():
        if name not in measurements:
            if status == "passed":
                raise ContractError(
                    "passed %s check requires measurement %s" % (check_id, name)
                )
            continue
        value = measurements[name]
        kind = rule["type"]
        if kind == "boolean":
            valid_type = type(value) is bool
        elif kind == "integer":
            valid_type = type(value) is int
        elif kind == "number":
            valid_type = type(value) is int or (
                type(value) is float and math.isfinite(value)
            )
        elif kind == "string":
            valid_type = isinstance(value, str)
        else:  # pragma: no cover - guarded by this module's constant table
            raise RuntimeError("unknown Workshop CAD measurement type %r" % kind)
        if not valid_type:
            raise ContractError(
                "%s measurement %s must be %s" % (check_id, name, kind)
            )
        if "minimum" in rule and value < rule["minimum"]:
            raise ContractError(
                "%s measurement %s must be at least %s"
                % (check_id, name, rule["minimum"])
            )
        if "min_length" in rule and len(value.strip()) < rule["min_length"]:
            raise ContractError(
                "%s measurement %s must be a non-empty string" % (check_id, name)
            )
        if status != "passed":
            continue
        if "pass_value" in rule and value != rule["pass_value"]:
            raise ContractError(
                "passed %s check requires %s=%r"
                % (check_id, name, rule["pass_value"])
            )
        if "pass_minimum" in rule and value < rule["pass_minimum"]:
            raise ContractError(
                "passed %s check requires %s >= %s"
                % (check_id, name, rule["pass_minimum"])
            )
        if "pass_maximum" in rule and value > rule["pass_maximum"]:
            raise ContractError(
                "passed %s check requires %s <= %s"
                % (check_id, name, rule["pass_maximum"])
            )


@dataclass(frozen=True)
class CadPart:
    part_id: str
    name: str
    quantity: int
    source_path: str
    step_path: str
    stl_path: str
    material: str
    print_orientation: Sequence[float]
    expected_solids: int = 1
    expected_shells: int = 1

    def __post_init__(self) -> None:
        self.assert_valid()

    def assert_valid(self) -> None:
        if not all(
            isinstance(value, str) and value
            for value in (self.part_id, self.name, self.material)
        ):
            raise ContractError("CAD part id, name, and material are required")
        if not all(
            type(value) is int and value > 0
            for value in (self.quantity, self.expected_solids, self.expected_shells)
        ):
            raise ContractError("CAD quantities and expected topology counts must be positive")
        _path(self.source_path, "part source_path")
        _path(self.step_path, "part step_path")
        _path(self.stl_path, "part stl_path")
        if (
            isinstance(self.print_orientation, (str, bytes))
            or not isinstance(self.print_orientation, Sequence)
            or len(self.print_orientation) != 3
        ):
            raise ContractError("print_orientation must contain three rotation degrees")
        if not all(
            type(value) is int or (type(value) is float and math.isfinite(value))
            for value in self.print_orientation
        ):
            raise ContractError("print_orientation values must be finite numbers")


@dataclass(frozen=True)
class PhysicalClaim:
    claim_id: str
    statement: str
    critical: bool
    status: str
    evidence_ref: Optional[str] = None
    evidence_sha256: Optional[str] = None

    def __post_init__(self) -> None:
        self.assert_valid()

    def assert_valid(self) -> None:
        if not all(
            isinstance(value, str) and value
            for value in (self.claim_id, self.statement)
        ):
            raise ContractError("physical claim id and statement are required")
        if type(self.critical) is not bool:
            raise ContractError("physical claim critical must be boolean")
        if not isinstance(self.status, str) or self.status not in RESULTS:
            raise ContractError("physical claim status must be passed, failed, or held")
        if (self.evidence_ref is None) != (self.evidence_sha256 is None):
            raise ContractError("physical claim evidence needs both a path and SHA-256")
        if self.evidence_ref is not None:
            _path(self.evidence_ref, "physical claim evidence_ref")
            require_sha256(self.evidence_sha256, "physical claim evidence_sha256")
        if self.status == "passed" and self.evidence_ref is None:
            raise ContractError("a passed physical claim requires hash-bound evidence")


@dataclass(frozen=True)
class CadProjectManifest:
    schema_version: int
    project_id: str
    artifact_sha256: str
    engine: Mapping[str, str]
    skill_versions: Mapping[str, str]
    parts: Sequence[CadPart]
    assemblies: Sequence[Mapping[str, Any]]
    fits: Sequence[Mapping[str, Any]]
    motions: Sequence[Mapping[str, Any]]
    print_profile: Mapping[str, Any]
    evidence_files: Mapping[str, str]
    physical_claims: Sequence[PhysicalClaim]

    def __post_init__(self) -> None:
        self.assert_valid()

    def assert_valid(self) -> None:
        if (
            type(self.schema_version) is not int
            or self.schema_version != 1
            or not isinstance(self.project_id, str)
            or not self.project_id
        ):
            raise ContractError("CAD manifest schema_version=1 and project_id are required")
        require_sha256(self.artifact_sha256, "CAD artifact_sha256")
        if not isinstance(self.engine, Mapping) or set(self.engine) != {"name", "version"}:
            raise ContractError("CAD engine must be an object")
        require_json_mapping(self.engine, "CAD engine")
        if (
            not isinstance(self.engine.get("name"), str)
            or not self.engine.get("name")
            or self.engine.get("name").casefold() in {"self-report", "trust-me"}
        ):
            raise ContractError("CAD engine name and version are required")
        require_exact_version(self.engine.get("version"), "CAD engine version")
        if not isinstance(self.skill_versions, Mapping) or not self.skill_versions:
            raise ContractError("CAD manifest must pin at least one skill version")
        require_json_mapping(self.skill_versions, "CAD skill_versions")
        for name, version in self.skill_versions.items():
            if not isinstance(name, str) or not name:
                raise ContractError("CAD skill version keys must be named")
            require_sha256(version, "CAD skill version %s" % name)
        if (
            isinstance(self.parts, (str, bytes))
            or not isinstance(self.parts, Sequence)
            or not self.parts
            or not all(isinstance(part, CadPart) for part in self.parts)
        ):
            raise ContractError("CAD project must declare at least one canonical part")
        for part in self.parts:
            part.assert_valid()
        ids = [part.part_id for part in self.parts]
        if len(ids) != len(set(ids)):
            raise ContractError("CAD part ids must be unique")
        paths = [
            path
            for part in self.parts
            for path in (part.source_path, part.step_path, part.stl_path)
        ]
        if len(paths) != len(set(paths)):
            raise ContractError("CAD source and export paths must be unique")
        if not isinstance(self.print_profile, Mapping):
            raise ContractError("CAD print_profile must be an object")
        require_json_mapping(self.print_profile, "CAD print_profile")
        if (
            not isinstance(self.print_profile.get("process"), str)
            or not self.print_profile.get("process")
        ):
            raise ContractError("CAD print_profile must declare a process")
        require_sha256(
            self.print_profile.get("profile_sha256"), "CAD print profile_sha256"
        )
        if not isinstance(self.evidence_files, Mapping):
            raise ContractError("CAD evidence_files must be a path-to-SHA object")
        require_json_mapping(self.evidence_files, "CAD evidence_files")
        for path, digest in self.evidence_files.items():
            _path(path, "CAD evidence file")
            require_sha256(digest, "CAD evidence file SHA-256")
        if (
            isinstance(self.physical_claims, (str, bytes))
            or not isinstance(self.physical_claims, Sequence)
            or not self.physical_claims
            or not all(
                isinstance(claim, PhysicalClaim) for claim in self.physical_claims
            )
        ):
            raise ContractError("CAD project must declare its physical claims")
        for claim in self.physical_claims:
            claim.assert_valid()
        claim_ids = [claim.claim_id for claim in self.physical_claims]
        if len(claim_ids) != len(set(claim_ids)):
            raise ContractError("CAD physical claim ids must be unique")
        for label, values in (
            ("assemblies", self.assemblies),
            ("fits", self.fits),
            ("motions", self.motions),
        ):
            if (
                isinstance(values, (str, bytes))
                or not isinstance(values, Sequence)
                or not all(isinstance(value, Mapping) for value in values)
            ):
                raise ContractError("CAD %s entries must be objects" % label)
            for value in values:
                require_json_mapping(value, "CAD %s entry" % label)

    def to_dict(self) -> Dict[str, Any]:
        self.assert_valid()
        return {
            "schema_version": self.schema_version,
            "project_id": self.project_id,
            "artifact_sha256": self.artifact_sha256,
            "engine": _plain_json(self.engine),
            "skill_versions": _plain_json(self.skill_versions),
            "parts": [
                {
                    "part_id": part.part_id,
                    "name": part.name,
                    "quantity": part.quantity,
                    "source_path": part.source_path,
                    "step_path": part.step_path,
                    "stl_path": part.stl_path,
                    "material": part.material,
                    "print_orientation": list(part.print_orientation),
                    "expected_solids": part.expected_solids,
                    "expected_shells": part.expected_shells,
                }
                for part in self.parts
            ],
            "assemblies": _plain_json(self.assemblies),
            "fits": _plain_json(self.fits),
            "motions": _plain_json(self.motions),
            "print_profile": _plain_json(self.print_profile),
            "evidence_files": _plain_json(self.evidence_files),
            "physical_claims": [asdict(claim) for claim in self.physical_claims],
        }


@dataclass(frozen=True)
class VerificationCheck:
    check_id: str
    status: str
    measurements: Mapping[str, Any]
    evidence_ref: str
    evidence_sha256: str
    limitations: Sequence[str] = ()

    def __post_init__(self) -> None:
        self.assert_valid()

    def assert_valid(self) -> None:
        """Revalidate mutable measurement mappings at every trust boundary."""
        if (
            not isinstance(self.check_id, str)
            or not self.check_id
            or not isinstance(self.status, str)
            or self.status not in RESULTS
        ):
            raise ContractError("verification check needs an id and valid status")
        if not isinstance(self.measurements, Mapping):
            raise ContractError("verification measurements must be an object")
        require_json_mapping(self.measurements, "verification measurements")
        if self.status == "passed" and not self.measurements:
            raise ContractError("a passed verification check needs measured evidence")
        _validate_workshop_measurements(self.check_id, self.status, self.measurements)
        _path(self.evidence_ref, "verification check evidence_ref")
        require_sha256(self.evidence_sha256, "verification check evidence_sha256")
        if (
            isinstance(self.limitations, (str, bytes))
            or not isinstance(self.limitations, Sequence)
            or not all(isinstance(item, str) and item for item in self.limitations)
        ):
            raise ContractError("verification limitations must be non-empty strings")


@dataclass(frozen=True)
class ValidatorRequirement:
    validator: str
    validator_version: str
    config_sha256: str
    substrate: str
    required_checks: Sequence[str]

    def __post_init__(self) -> None:
        self.assert_valid()

    def assert_valid(self) -> None:
        if (
            not isinstance(self.validator, str)
            or not self.validator
            or self.validator.casefold() in {"self-report", "trust-me"}
        ):
            raise ContractError("validator policy requires an exact name and version")
        require_exact_version(self.validator_version, "validator policy version")
        require_sha256(self.config_sha256, "validator policy config_sha256")
        if not isinstance(self.substrate, str) or self.substrate not in SUBSTRATES:
            raise ContractError("validator policy substrate is not recognized")
        if (
            isinstance(self.required_checks, (str, bytes))
            or not isinstance(self.required_checks, Sequence)
            or not self.required_checks
            or not all(isinstance(item, str) and item for item in self.required_checks)
            or len(self.required_checks) != len(set(self.required_checks))
        ):
            raise ContractError("validator policy requires unique named checks")


@dataclass(frozen=True)
class VerificationReceipt:
    schema_version: int
    artifact_sha256: str
    validator: str
    validator_version: str
    config_sha256: str
    substrate: str
    status: str
    checks: Sequence[VerificationCheck]
    observed_at: str

    def __post_init__(self) -> None:
        self.assert_valid()

    def assert_valid(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ContractError("verification receipt schema_version must be 1")
        require_sha256(self.artifact_sha256, "verification artifact_sha256")
        require_sha256(self.config_sha256, "verification config_sha256")
        if (
            not isinstance(self.validator, str)
            or not self.validator
            or self.validator.casefold() in {"self-report", "trust-me"}
        ):
            raise ContractError("verification validator and version are required")
        require_exact_version(self.validator_version, "verification validator version")
        if not isinstance(self.substrate, str) or self.substrate not in SUBSTRATES:
            raise ContractError("verification substrate is not recognized")
        if not isinstance(self.status, str) or self.status not in RESULTS:
            raise ContractError("verification status must be passed, failed, or held")
        if (
            isinstance(self.checks, (str, bytes))
            or not isinstance(self.checks, Sequence)
            or not self.checks
        ):
            raise ContractError("verification receipt cannot be empty")
        if not all(isinstance(check, VerificationCheck) for check in self.checks):
            raise ContractError("verification receipt checks have an invalid type")
        for check in self.checks:
            check.assert_valid()
        ids = [check.check_id for check in self.checks]
        if len(ids) != len(set(ids)):
            raise ContractError("verification check ids must be unique")
        derived = "failed" if any(check.status == "failed" for check in self.checks) else (
            "held" if any(check.status == "held" for check in self.checks) else "passed"
        )
        if self.status != derived:
            raise ContractError("receipt status must equal the worst check status")
        require_utc_timestamp(self.observed_at, "verification observed_at")

    @classmethod
    def create(
        cls,
        artifact_sha256: str,
        validator: str,
        validator_version: str,
        config_sha256: str,
        substrate: str,
        checks: Sequence[VerificationCheck],
    ) -> "VerificationReceipt":
        status = "failed" if any(check.status == "failed" for check in checks) else (
            "held" if any(check.status == "held" for check in checks) else "passed"
        )
        return cls(
            1,
            artifact_sha256,
            validator,
            validator_version,
            config_sha256,
            substrate,
            status,
            tuple(checks),
            utc_now(),
        )

    def to_dict(self) -> Dict[str, Any]:
        self.assert_valid()
        return {
            "schema_version": self.schema_version,
            "artifact_sha256": self.artifact_sha256,
            "validator": self.validator,
            "validator_version": self.validator_version,
            "config_sha256": self.config_sha256,
            "substrate": self.substrate,
            "status": self.status,
            "checks": [
                {
                    "check_id": check.check_id,
                    "status": check.status,
                    "measurements": _plain_json(check.measurements),
                    "evidence_ref": check.evidence_ref,
                    "evidence_sha256": check.evidence_sha256,
                    "limitations": list(check.limitations),
                }
                for check in self.checks
            ],
            "observed_at": self.observed_at,
        }


@dataclass(frozen=True)
class CadReleaseBundle:
    """A canonical, already-validated CAD release decision.

    The identity is over the project manifest, exact validator policy, and all
    receipts.  Lifecycle gates bind to this identity instead of trusting a
    free-form Boolean labelled ``cad``.
    """

    manifest: CadProjectManifest
    receipts: Sequence[VerificationReceipt]
    requirements: Sequence[ValidatorRequirement]

    def __post_init__(self) -> None:
        self.assert_valid()

    def assert_valid(self) -> None:
        assert_release_ready(self.manifest, self.receipts, self.requirements)

    @property
    def sha256(self) -> str:
        self.assert_valid()
        document = {
            "manifest": self.manifest.to_dict(),
            "receipts": [
                receipt.to_dict()
                for receipt in sorted(self.receipts, key=lambda item: item.validator)
            ],
            "requirements": [
                {
                    "validator": requirement.validator,
                    "validator_version": requirement.validator_version,
                    "config_sha256": requirement.config_sha256,
                    "substrate": requirement.substrate,
                    "required_checks": list(requirement.required_checks),
                }
                for requirement in sorted(
                    self.requirements, key=lambda item: item.validator
                )
            ],
        }
        canonical = json.dumps(
            document,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()

    def assert_artifact(self, artifact_sha256: str) -> None:
        self.assert_valid()
        if self.manifest.artifact_sha256 != artifact_sha256:
            raise TransitionError("CAD release bundle belongs to different artifact bytes")


def assert_release_ready(
    manifest: CadProjectManifest,
    receipts: Sequence[VerificationReceipt],
    requirements: Sequence[ValidatorRequirement],
) -> None:
    """Fail closed when evidence is missing, stale, held, failed, or duplicated."""
    if not isinstance(manifest, CadProjectManifest):
        raise TransitionError("CAD release manifest has an invalid type")
    if (
        isinstance(receipts, (str, bytes))
        or not isinstance(receipts, Sequence)
        or isinstance(requirements, (str, bytes))
        or not isinstance(requirements, Sequence)
    ):
        raise TransitionError("CAD release receipts and validator policy must be sequences")
    if not receipts or not requirements:
        raise TransitionError("CAD release requires non-empty receipts and validator policy")
    if not all(isinstance(receipt, VerificationReceipt) for receipt in receipts):
        raise TransitionError("CAD release receipts have an invalid type")
    if not all(
        isinstance(requirement, ValidatorRequirement) for requirement in requirements
    ):
        raise TransitionError("CAD validator policy has an invalid type")
    try:
        manifest.assert_valid()
        for receipt in receipts:
            receipt.assert_valid()
        for requirement in requirements:
            requirement.assert_valid()
    except ContractError as exc:
        raise TransitionError(
            "CAD release contains a mutated or invalid nested contract"
        ) from exc
    policy = {item.validator: item for item in requirements}
    if len(policy) != len(requirements):
        raise TransitionError("CAD validator policy contains duplicate names")
    policy_checks = {check for item in requirements for check in item.required_checks}
    minimum_checks = set(WORKSHOP_REQUIRED_CHECKS)
    if any(claim.critical for claim in manifest.physical_claims):
        minimum_checks.add("physical-claims")
    missing_floor = minimum_checks - policy_checks
    if missing_floor:
        raise TransitionError("CAD validator policy waives Workshop checks: %s" % sorted(missing_floor))
    required_substrates = {"deterministic", "independent-review"}
    if any(claim.critical for claim in manifest.physical_claims):
        required_substrates.add("physical")
    configured_substrates = {item.substrate for item in requirements}
    if not required_substrates <= configured_substrates:
        raise TransitionError(
            "CAD validator policy lacks independent substrates: %s"
            % sorted(required_substrates - configured_substrates)
        )
    pinned_hashes = [
        manifest.artifact_sha256,
        manifest.print_profile.get("profile_sha256"),
        *manifest.skill_versions.values(),
        *(item.config_sha256 for item in requirements),
    ]
    if any(value == ZERO_SHA256 for value in pinned_hashes):
        raise TransitionError("CAD release contains a template or unpinned zero hash")
    by_validator = {}
    checks = {}
    for receipt in receipts:
        if receipt.artifact_sha256 != manifest.artifact_sha256:
            raise TransitionError("CAD verification receipt is stale or for different bytes")
        if receipt.validator in by_validator:
            raise TransitionError("duplicate CAD validator receipt %r" % receipt.validator)
        by_validator[receipt.validator] = receipt
        if receipt.status != "passed":
            raise TransitionError(
                "CAD validator %s is %s" % (receipt.validator, receipt.status)
            )
        for check in receipt.checks:
            if check.check_id in checks:
                raise TransitionError("duplicate CAD check %r" % check.check_id)
            checks[check.check_id] = check
            expected_substrate = WORKSHOP_CHECK_SUBSTRATES.get(check.check_id)
            if expected_substrate is not None and receipt.substrate != expected_substrate:
                raise TransitionError(
                    "CAD check %s came from %s, expected %s"
                    % (check.check_id, receipt.substrate, expected_substrate)
                )
            if manifest.evidence_files.get(check.evidence_ref) != check.evidence_sha256:
                raise TransitionError(
                    "CAD check %s evidence is absent or hash-mismatched in the artifact"
                    % check.check_id
                )
    if set(by_validator) != set(policy):
        raise TransitionError(
            "CAD receipts do not match pinned validators (got %s, require %s)"
            % (sorted(by_validator), sorted(policy))
        )
    for validator, requirement in policy.items():
        receipt = by_validator[validator]
        if (
            receipt.validator_version != requirement.validator_version
            or receipt.config_sha256 != requirement.config_sha256
            or receipt.substrate != requirement.substrate
        ):
            raise TransitionError("CAD validator %s version/config drift" % validator)
        receipt_checks = {check.check_id: check for check in receipt.checks}
        missing = set(requirement.required_checks) - set(receipt_checks)
        if missing:
            raise TransitionError(
                "CAD validator %s lacks checks: %s" % (validator, sorted(missing))
            )
        if any(receipt_checks[name].status != "passed" for name in requirement.required_checks):
            raise TransitionError("a required CAD check is not passed")
    blocked_claims = [
        claim.claim_id
        for claim in manifest.physical_claims
        if claim.critical and claim.status != "passed"
    ]
    if blocked_claims:
        raise TransitionError(
            "critical physical claims are not proven: %s" % sorted(blocked_claims)
        )
    for claim in manifest.physical_claims:
        if claim.status == "passed" and (
            claim.evidence_ref is None
            or manifest.evidence_files.get(claim.evidence_ref) != claim.evidence_sha256
        ):
            raise TransitionError(
                "physical claim %s evidence is absent or hash-mismatched in the artifact"
                % claim.claim_id
            )
