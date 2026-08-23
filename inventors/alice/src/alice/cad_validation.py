"""Fail-closed CAD facts adapted from Peter's ``text-to-3d`` work.

The fit derivation model is adapted from
``skills/cad/scripts/cadfits.py`` and the STL topology algorithm is adapted
from ``skills/cad/scripts/check_mesh`` at upstream commit
``f18aebe4698d92ffccf07d94e2d624b08d30e667``.  Those sources are MIT licensed
by Thompson Labs LLC; :data:`UPSTREAM_MIT_NOTICE` preserves the notice.

This module deliberately narrows the upstream claims.  Calibration values are
never universal defaults: every derivation is bound to a versioned printer,
nozzle, layer-height, material, and calibration-evidence hash.  An STL topology
pass means only that the supplied bytes passed the declared, bounded topology
checks.  It does not establish CAD-kernel solidness, wall thickness, overhangs,
slicer success, manufacturability, or physical fit.  Motion evaluators likewise
must return a conclusive, hash-bound boolean; an exception, missing fact, or
inconclusive result can never satisfy either a clear or blocked expectation.
"""

from __future__ import annotations

import hashlib
import json
import math
import struct
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any


UPSTREAM_SOURCE_COMMIT = "f18aebe4698d92ffccf07d94e2d624b08d30e667"
UPSTREAM_SOURCE_PATHS = (
    "skills/cad/scripts/cadfits.py",
    "skills/cad/scripts/check_mesh",
)
UPSTREAM_MIT_NOTICE = """MIT License

Copyright (c) 2026 Thompson Labs LLC

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

CALIBRATION_PROFILE_VERSION = "alice.printer-calibration-profile.v1"
PROFILE_BINDING_RECEIPT_VERSION = "alice.printer-profile-binding-receipt.v1"
PROFILE_SELF_CHECK_RECEIPT_VERSION = "alice.printer-profile-self-check-receipt.v1"
ASSEMBLED_FIT_RECEIPT_VERSION = "alice.assembled-fit-receipt.v1"
PRINT_IN_PLACE_RECEIPT_VERSION = "alice.print-in-place-fit-receipt.v1"
STL_INSPECTION_RECEIPT_VERSION = "alice.stl-topology-receipt.v1"
KERNEL_BODY_OBSERVATION_VERSION = "alice.kernel-body-observation.v1"
MOTION_CONDITION_VERSION = "alice.motion-condition.v1"
MOTION_OUTCOME_VERSION = "alice.motion-evaluator-outcome.v1"
MOTION_RECEIPT_VERSION = "alice.motion-validation-receipt.v1"

_HEX = frozenset("0123456789abcdef")
_ASSEMBLED_LIMITATIONS = (
    "nominal_dimension_derivation_only",
    "profile_values_require_physical_calibration_for_the_bound_machine_and_material",
    "not_physical_fit_evidence",
)
_PIP_LIMITATIONS = (
    "profile_lookup_only",
    "rigid_geometry_does_not_prove_a_print_in_place_joint_will_release_or_move",
    "not_physical_fit_evidence",
)
_STL_LIMITATIONS = (
    "stl_topology_only_not_cad_kernel_solidness",
    "does_not_measure_wall_thickness_overhang_slicer_success_or_physical_fit",
)
_MOTION_LIMITATIONS = (
    "sampled_rigid_body_evidence_only",
    "does_not_establish_elastic_deformation_friction_retention_or_physical_fit",
)


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _finite_number(value: object, field: str) -> float:
    if not _is_number(value):
        raise TypeError(f"{field} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{field} must be finite")
    return result


def _positive_number(value: object, field: str) -> float:
    result = _finite_number(value, field)
    if result <= 0:
        raise ValueError(f"{field} must be > 0")
    return result


def _nonempty_string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    result = value.strip()
    if any(ord(character) < 32 for character in result):
        raise ValueError(f"{field} must not contain control characters")
    return result


def _sha256(value: object, field: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or value.lower() != value
        or any(character not in _HEX for character in value)
    ):
        raise ValueError(f"{field} must be a lowercase SHA-256 digest")
    return value


def _json_copy(value: object, field: str, *, max_nodes: int = 20_000) -> Any:
    """Return a JSON-only deep copy without silently stringifying map keys."""

    nodes = 0

    def visit(item: object, depth: int) -> Any:
        nonlocal nodes
        nodes += 1
        if nodes > max_nodes:
            raise ValueError(f"{field} exceeds the JSON node limit")
        if depth > 32:
            raise ValueError(f"{field} exceeds the JSON nesting limit")
        if item is None or isinstance(item, (str, bool, int)):
            return item
        if isinstance(item, float):
            if not math.isfinite(item):
                raise ValueError(f"{field} contains a non-finite number")
            return item
        if isinstance(item, Mapping):
            copied: dict[str, Any] = {}
            for key, child in item.items():
                if not isinstance(key, str):
                    raise TypeError(f"{field} object keys must be strings")
                copied[key] = visit(child, depth + 1)
            return copied
        if isinstance(item, (list, tuple)):
            return [visit(child, depth + 1) for child in item]
        raise TypeError(f"{field} contains a non-JSON value {type(item).__name__}")

    return visit(value, 0)


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def _canonical_sha256(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class AssembledFitCalibration:
    """One named, calibrated per-side clearance for separately printed parts."""

    name: str
    per_side_clearance_mm: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _nonempty_string(self.name, "fit name"))
        object.__setattr__(
            self,
            "per_side_clearance_mm",
            _finite_number(self.per_side_clearance_mm, "per_side_clearance_mm"),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "per_side_clearance_mm": self.per_side_clearance_mm,
        }


@dataclass(frozen=True, slots=True)
class PrintInPlaceFitCalibration:
    """Calibrated face gaps for parts printed together in one job."""

    name: str
    xy_gap_mm: float
    z_gap_mm: float
    bottom_relief_mm: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _nonempty_string(self.name, "fit name"))
        xy = _positive_number(self.xy_gap_mm, "xy_gap_mm")
        z = _positive_number(self.z_gap_mm, "z_gap_mm")
        bottom = _finite_number(self.bottom_relief_mm, "bottom_relief_mm")
        if bottom < 0:
            raise ValueError("bottom_relief_mm must be >= 0")
        if z <= xy:
            raise ValueError("z_gap_mm must be greater than xy_gap_mm")
        object.__setattr__(self, "xy_gap_mm", xy)
        object.__setattr__(self, "z_gap_mm", z)
        object.__setattr__(self, "bottom_relief_mm", bottom)

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "xy_gap_mm": self.xy_gap_mm,
            "z_gap_mm": self.z_gap_mm,
            "bottom_relief_mm": self.bottom_relief_mm,
        }


@dataclass(frozen=True, slots=True)
class PrinterCalibrationProfile:
    """A versioned calibration bound to one exact print configuration.

    There is intentionally no built-in PLA/0.4-mm profile.  A caller must
    provide measurements and bind them to its own evidence artifact.
    """

    profile_id: str
    revision: int
    printer_id: str
    nozzle_diameter_mm: float
    layer_height_mm: float
    material: str
    calibration_evidence_sha256: str
    assembled_fits: tuple[AssembledFitCalibration, ...]
    print_in_place_fits: tuple[PrintInPlaceFitCalibration, ...]
    schema_version: str = CALIBRATION_PROFILE_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != CALIBRATION_PROFILE_VERSION:
            raise ValueError(
                f"unsupported calibration profile version {self.schema_version!r}"
            )
        object.__setattr__(
            self, "profile_id", _nonempty_string(self.profile_id, "profile_id")
        )
        object.__setattr__(
            self, "printer_id", _nonempty_string(self.printer_id, "printer_id")
        )
        object.__setattr__(self, "material", _nonempty_string(self.material, "material"))
        if (
            isinstance(self.revision, bool)
            or not isinstance(self.revision, int)
            or self.revision < 1
        ):
            raise ValueError("revision must be a positive integer")
        object.__setattr__(
            self,
            "nozzle_diameter_mm",
            _positive_number(self.nozzle_diameter_mm, "nozzle_diameter_mm"),
        )
        object.__setattr__(
            self,
            "layer_height_mm",
            _positive_number(self.layer_height_mm, "layer_height_mm"),
        )
        object.__setattr__(
            self,
            "calibration_evidence_sha256",
            _sha256(self.calibration_evidence_sha256, "calibration_evidence_sha256"),
        )
        assembled = tuple(self.assembled_fits)
        pip = tuple(self.print_in_place_fits)
        if not assembled:
            raise ValueError("assembled_fits must not be empty")
        if not pip:
            raise ValueError("print_in_place_fits must not be empty")
        if any(not isinstance(item, AssembledFitCalibration) for item in assembled):
            raise TypeError("assembled_fits must contain AssembledFitCalibration values")
        if any(not isinstance(item, PrintInPlaceFitCalibration) for item in pip):
            raise TypeError("print_in_place_fits must contain PrintInPlaceFitCalibration values")
        if len({item.name for item in assembled}) != len(assembled):
            raise ValueError("assembled fit names must be unique")
        if len({item.name for item in pip}) != len(pip):
            raise ValueError("print-in-place fit names must be unique")
        object.__setattr__(
            self,
            "assembled_fits",
            tuple(sorted(assembled, key=lambda item: item.name)),
        )
        object.__setattr__(
            self,
            "print_in_place_fits",
            tuple(sorted(pip, key=lambda item: item.name)),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "profile_id": self.profile_id,
            "revision": self.revision,
            "printer_id": self.printer_id,
            "nozzle_diameter_mm": self.nozzle_diameter_mm,
            "layer_height_mm": self.layer_height_mm,
            "material": self.material,
            "calibration_evidence_sha256": self.calibration_evidence_sha256,
            "assembled_fits": [fit.to_dict() for fit in self.assembled_fits],
            "print_in_place_fits": [fit.to_dict() for fit in self.print_in_place_fits],
        }

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "PrinterCalibrationProfile":
        """Load a profile from JSON-shaped data without accepting loose types."""

        if not isinstance(raw, Mapping):
            raise TypeError("calibration profile must be an object")
        allowed = {
            "schema_version",
            "profile_id",
            "revision",
            "printer_id",
            "nozzle_diameter_mm",
            "layer_height_mm",
            "material",
            "calibration_evidence_sha256",
            "assembled_fits",
            "print_in_place_fits",
        }
        unknown = sorted(set(raw) - allowed)
        if unknown:
            raise ValueError(f"unknown calibration profile fields: {', '.join(unknown)}")
        assembled_raw = raw.get("assembled_fits")
        pip_raw = raw.get("print_in_place_fits")
        if not isinstance(assembled_raw, list) or not all(
            isinstance(item, Mapping) for item in assembled_raw
        ):
            raise TypeError("assembled_fits must be a list of objects")
        if not isinstance(pip_raw, list) or not all(
            isinstance(item, Mapping) for item in pip_raw
        ):
            raise TypeError("print_in_place_fits must be a list of objects")
        if any(set(item) != {"name", "per_side_clearance_mm"} for item in assembled_raw):
            raise ValueError("assembled fit fields must be name and per_side_clearance_mm")
        if any(
            set(item) != {"name", "xy_gap_mm", "z_gap_mm", "bottom_relief_mm"}
            for item in pip_raw
        ):
            raise ValueError(
                "print-in-place fit fields must be name, xy_gap_mm, z_gap_mm, "
                "and bottom_relief_mm"
            )
        return cls(
            schema_version=raw.get("schema_version", CALIBRATION_PROFILE_VERSION),
            profile_id=raw.get("profile_id"),
            revision=raw.get("revision"),
            printer_id=raw.get("printer_id"),
            nozzle_diameter_mm=raw.get("nozzle_diameter_mm"),
            layer_height_mm=raw.get("layer_height_mm"),
            material=raw.get("material"),
            calibration_evidence_sha256=raw.get("calibration_evidence_sha256"),
            assembled_fits=tuple(
                AssembledFitCalibration(
                    name=item.get("name"),
                    per_side_clearance_mm=item.get("per_side_clearance_mm"),
                )
                for item in assembled_raw
            ),
            print_in_place_fits=tuple(
                PrintInPlaceFitCalibration(
                    name=item.get("name"),
                    xy_gap_mm=item.get("xy_gap_mm"),
                    z_gap_mm=item.get("z_gap_mm"),
                    bottom_relief_mm=item.get("bottom_relief_mm"),
                )
                for item in pip_raw
            ),
        )

    @property
    def profile_sha256(self) -> str:
        return _canonical_sha256(self.to_dict())

    def assembled_fit(self, name: str) -> AssembledFitCalibration:
        for fit in self.assembled_fits:
            if fit.name == name:
                return fit
        raise ValueError(f"unknown assembled fit class {name!r}")

    def print_in_place_fit(self, name: str) -> PrintInPlaceFitCalibration:
        for fit in self.print_in_place_fits:
            if fit.name == name:
                return fit
        raise ValueError(f"unknown print-in-place fit class {name!r}")


@dataclass(frozen=True, slots=True)
class PrinterTarget:
    """The actual job configuration that a calibration must match exactly."""

    profile_id: str
    profile_revision: int
    printer_id: str
    nozzle_diameter_mm: float
    layer_height_mm: float
    material: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "profile_id", _nonempty_string(self.profile_id, "profile_id")
        )
        object.__setattr__(
            self, "printer_id", _nonempty_string(self.printer_id, "printer_id")
        )
        object.__setattr__(self, "material", _nonempty_string(self.material, "material"))
        if (
            isinstance(self.profile_revision, bool)
            or not isinstance(self.profile_revision, int)
            or self.profile_revision < 1
        ):
            raise ValueError("profile_revision must be a positive integer")
        object.__setattr__(
            self,
            "nozzle_diameter_mm",
            _positive_number(self.nozzle_diameter_mm, "nozzle_diameter_mm"),
        )
        object.__setattr__(
            self,
            "layer_height_mm",
            _positive_number(self.layer_height_mm, "layer_height_mm"),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "profile_id": self.profile_id,
            "profile_revision": self.profile_revision,
            "printer_id": self.printer_id,
            "nozzle_diameter_mm": self.nozzle_diameter_mm,
            "layer_height_mm": self.layer_height_mm,
            "material": self.material,
        }

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "PrinterTarget":
        if not isinstance(raw, Mapping):
            raise TypeError("printer target must be an object")
        allowed = {
            "profile_id",
            "profile_revision",
            "printer_id",
            "nozzle_diameter_mm",
            "layer_height_mm",
            "material",
        }
        unknown = sorted(set(raw) - allowed)
        if unknown:
            raise ValueError(f"unknown printer target fields: {', '.join(unknown)}")
        return cls(
            profile_id=raw.get("profile_id"),
            profile_revision=raw.get("profile_revision"),
            printer_id=raw.get("printer_id"),
            nozzle_diameter_mm=raw.get("nozzle_diameter_mm"),
            layer_height_mm=raw.get("layer_height_mm"),
            material=raw.get("material"),
        )

    @property
    def target_sha256(self) -> str:
        return _canonical_sha256(self.to_dict())


@dataclass(frozen=True, slots=True)
class ProfileBindingReceipt:
    schema_version: str
    status: str
    profile_id: str
    profile_revision: int
    profile_sha256: str
    target_sha256: str
    mismatches: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "profile_id": self.profile_id,
            "profile_revision": self.profile_revision,
            "profile_sha256": self.profile_sha256,
            "target_sha256": self.target_sha256,
            "mismatches": list(self.mismatches),
        }

    @property
    def receipt_sha256(self) -> str:
        return _canonical_sha256(self.to_dict())


def validate_profile_binding(
    profile: PrinterCalibrationProfile, target: PrinterTarget
) -> ProfileBindingReceipt:
    """Return a fail-closed receipt for a profile/job configuration binding."""

    mismatches: list[str] = []
    if target.profile_id != profile.profile_id:
        mismatches.append("profile_id_mismatch")
    if target.profile_revision != profile.revision:
        mismatches.append("profile_revision_mismatch")
    if target.printer_id != profile.printer_id:
        mismatches.append("printer_id_mismatch")
    if target.nozzle_diameter_mm != profile.nozzle_diameter_mm:
        mismatches.append("nozzle_diameter_mismatch")
    if target.layer_height_mm != profile.layer_height_mm:
        mismatches.append("layer_height_mismatch")
    if target.material.casefold() != profile.material.casefold():
        mismatches.append("material_mismatch")
    return ProfileBindingReceipt(
        schema_version=PROFILE_BINDING_RECEIPT_VERSION,
        status="passed" if not mismatches else "held",
        profile_id=profile.profile_id,
        profile_revision=profile.revision,
        profile_sha256=profile.profile_sha256,
        target_sha256=target.target_sha256,
        mismatches=tuple(mismatches),
    )


@dataclass(frozen=True, slots=True)
class ProfileSelfCheckReceipt:
    schema_version: str
    status: str
    profile_id: str
    profile_revision: int
    profile_sha256: str
    checks: tuple[str, ...]
    failures: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "profile_id": self.profile_id,
            "profile_revision": self.profile_revision,
            "profile_sha256": self.profile_sha256,
            "checks": list(self.checks),
            "failures": list(self.failures),
        }

    @property
    def receipt_sha256(self) -> str:
        return _canonical_sha256(self.to_dict())


def self_check_calibration_profile(
    profile: PrinterCalibrationProfile,
) -> ProfileSelfCheckReceipt:
    """Check algebraic invariants without pretending they are print evidence."""

    checks: list[str] = []
    failures: list[str] = []
    for fit in profile.assembled_fits:
        label = f"assembled_round_trip:{fit.name}"
        checks.append(label)
        nominal = max(1.0, abs(fit.per_side_clearance_mm) * 4.0 + 1.0)
        female = nominal + 2.0 * fit.per_side_clearance_mm
        round_trip = female - 2.0 * fit.per_side_clearance_mm
        if female <= 0 or not math.isclose(
            round_trip, nominal, rel_tol=0.0, abs_tol=1e-12
        ):
            failures.append(label)
    for fit in profile.print_in_place_fits:
        label = f"pip_z_exceeds_xy:{fit.name}"
        checks.append(label)
        if not fit.z_gap_mm > fit.xy_gap_mm:
            failures.append(label)
    return ProfileSelfCheckReceipt(
        schema_version=PROFILE_SELF_CHECK_RECEIPT_VERSION,
        status="passed" if not failures else "held",
        profile_id=profile.profile_id,
        profile_revision=profile.revision,
        profile_sha256=profile.profile_sha256,
        checks=tuple(checks),
        failures=tuple(failures),
    )


@dataclass(frozen=True, slots=True)
class AssembledFitReceipt:
    schema_version: str
    status: str
    profile_id: str
    profile_revision: int
    profile_sha256: str
    target_sha256: str
    fit_class: str
    owned_side: str
    owned_dimension_mm: float
    per_side_clearance_mm: float | None
    derived_side: str
    derived_dimension_mm: float | None
    formula: str
    reasons: tuple[str, ...]
    limitations: tuple[str, ...] = _ASSEMBLED_LIMITATIONS

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "profile_id": self.profile_id,
            "profile_revision": self.profile_revision,
            "profile_sha256": self.profile_sha256,
            "target_sha256": self.target_sha256,
            "fit_class": self.fit_class,
            "owned_side": self.owned_side,
            "owned_dimension_mm": self.owned_dimension_mm,
            "per_side_clearance_mm": self.per_side_clearance_mm,
            "derived_side": self.derived_side,
            "derived_dimension_mm": self.derived_dimension_mm,
            "formula": self.formula,
            "reasons": list(self.reasons),
            "limitations": list(self.limitations),
        }

    @property
    def receipt_sha256(self) -> str:
        return _canonical_sha256(self.to_dict())


def derive_assembled_fit(
    profile: PrinterCalibrationProfile,
    target: PrinterTarget,
    *,
    fit_class: str,
    owned_side: str,
    owned_dimension_mm: float,
) -> AssembledFitReceipt:
    """Derive the other half of a male/female interface from one owner."""

    fit_class = _nonempty_string(fit_class, "fit_class")
    if owned_side not in {"male", "female"}:
        raise ValueError("owned_side must be 'male' or 'female'")
    owned = _positive_number(owned_dimension_mm, "owned_dimension_mm")
    binding = validate_profile_binding(profile, target)
    derived_side = "female" if owned_side == "male" else "male"
    formula = (
        "female=male+2*per_side_clearance"
        if owned_side == "male"
        else "male=female-2*per_side_clearance"
    )
    try:
        calibration = profile.assembled_fit(fit_class)
    except ValueError:
        return AssembledFitReceipt(
            schema_version=ASSEMBLED_FIT_RECEIPT_VERSION,
            status="held",
            profile_id=profile.profile_id,
            profile_revision=profile.revision,
            profile_sha256=profile.profile_sha256,
            target_sha256=target.target_sha256,
            fit_class=fit_class,
            owned_side=owned_side,
            owned_dimension_mm=owned,
            per_side_clearance_mm=None,
            derived_side=derived_side,
            derived_dimension_mm=None,
            formula=formula,
            reasons=("unknown_fit_class",),
        )
    if binding.status != "passed":
        return AssembledFitReceipt(
            schema_version=ASSEMBLED_FIT_RECEIPT_VERSION,
            status="held",
            profile_id=profile.profile_id,
            profile_revision=profile.revision,
            profile_sha256=profile.profile_sha256,
            target_sha256=target.target_sha256,
            fit_class=fit_class,
            owned_side=owned_side,
            owned_dimension_mm=owned,
            per_side_clearance_mm=calibration.per_side_clearance_mm,
            derived_side=derived_side,
            derived_dimension_mm=None,
            formula=formula,
            reasons=binding.mismatches,
        )
    direction = 1.0 if owned_side == "male" else -1.0
    derived = owned + direction * 2.0 * calibration.per_side_clearance_mm
    if not math.isfinite(derived) or derived <= 0:
        return AssembledFitReceipt(
            schema_version=ASSEMBLED_FIT_RECEIPT_VERSION,
            status="failed",
            profile_id=profile.profile_id,
            profile_revision=profile.revision,
            profile_sha256=profile.profile_sha256,
            target_sha256=target.target_sha256,
            fit_class=fit_class,
            owned_side=owned_side,
            owned_dimension_mm=owned,
            per_side_clearance_mm=calibration.per_side_clearance_mm,
            derived_side=derived_side,
            derived_dimension_mm=None,
            formula=formula,
            reasons=("derived_dimension_nonpositive_or_nonfinite",),
        )
    return AssembledFitReceipt(
        schema_version=ASSEMBLED_FIT_RECEIPT_VERSION,
        status="passed",
        profile_id=profile.profile_id,
        profile_revision=profile.revision,
        profile_sha256=profile.profile_sha256,
        target_sha256=target.target_sha256,
        fit_class=fit_class,
        owned_side=owned_side,
        owned_dimension_mm=owned,
        per_side_clearance_mm=calibration.per_side_clearance_mm,
        derived_side=derived_side,
        derived_dimension_mm=derived,
        formula=formula,
        reasons=(),
    )


@dataclass(frozen=True, slots=True)
class PrintInPlaceFitReceipt:
    schema_version: str
    status: str
    profile_id: str
    profile_revision: int
    profile_sha256: str
    target_sha256: str
    fit_class: str
    xy_gap_mm: float | None
    z_gap_mm: float | None
    bottom_relief_mm: float | None
    reasons: tuple[str, ...]
    limitations: tuple[str, ...] = _PIP_LIMITATIONS

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "profile_id": self.profile_id,
            "profile_revision": self.profile_revision,
            "profile_sha256": self.profile_sha256,
            "target_sha256": self.target_sha256,
            "fit_class": self.fit_class,
            "xy_gap_mm": self.xy_gap_mm,
            "z_gap_mm": self.z_gap_mm,
            "bottom_relief_mm": self.bottom_relief_mm,
            "reasons": list(self.reasons),
            "limitations": list(self.limitations),
        }

    @property
    def receipt_sha256(self) -> str:
        return _canonical_sha256(self.to_dict())


def derive_print_in_place_fit(
    profile: PrinterCalibrationProfile,
    target: PrinterTarget,
    *,
    fit_class: str,
) -> PrintInPlaceFitReceipt:
    """Look up calibrated PIP gaps without applying universal material bumps."""

    fit_class = _nonempty_string(fit_class, "fit_class")
    binding = validate_profile_binding(profile, target)
    try:
        calibration = profile.print_in_place_fit(fit_class)
    except ValueError:
        return PrintInPlaceFitReceipt(
            schema_version=PRINT_IN_PLACE_RECEIPT_VERSION,
            status="held",
            profile_id=profile.profile_id,
            profile_revision=profile.revision,
            profile_sha256=profile.profile_sha256,
            target_sha256=target.target_sha256,
            fit_class=fit_class,
            xy_gap_mm=None,
            z_gap_mm=None,
            bottom_relief_mm=None,
            reasons=("unknown_fit_class",),
        )
    if binding.status != "passed":
        return PrintInPlaceFitReceipt(
            schema_version=PRINT_IN_PLACE_RECEIPT_VERSION,
            status="held",
            profile_id=profile.profile_id,
            profile_revision=profile.revision,
            profile_sha256=profile.profile_sha256,
            target_sha256=target.target_sha256,
            fit_class=fit_class,
            xy_gap_mm=None,
            z_gap_mm=None,
            bottom_relief_mm=None,
            reasons=binding.mismatches,
        )
    return PrintInPlaceFitReceipt(
        schema_version=PRINT_IN_PLACE_RECEIPT_VERSION,
        status="passed",
        profile_id=profile.profile_id,
        profile_revision=profile.revision,
        profile_sha256=profile.profile_sha256,
        target_sha256=target.target_sha256,
        fit_class=fit_class,
        xy_gap_mm=calibration.xy_gap_mm,
        z_gap_mm=calibration.z_gap_mm,
        bottom_relief_mm=calibration.bottom_relief_mm,
        reasons=(),
    )


@dataclass(frozen=True, slots=True)
class StlInspectionLimits:
    """Resource and numeric bounds for a single pure in-memory inspection."""

    max_source_bytes: int = 32 * 1024 * 1024
    max_triangles: int = 250_000
    weld_tolerance_mm: float = 1e-6
    degenerate_area_epsilon_mm2: float = 1e-18
    zero_volume_epsilon_mm3: float = 1e-12
    max_abs_coordinate_mm: float = 1_000_000.0

    def __post_init__(self) -> None:
        for field in ("max_source_bytes", "max_triangles"):
            value = getattr(self, field)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(f"{field} must be a positive integer")
        for field in ("weld_tolerance_mm", "max_abs_coordinate_mm"):
            object.__setattr__(self, field, _positive_number(getattr(self, field), field))
        for field in ("degenerate_area_epsilon_mm2", "zero_volume_epsilon_mm3"):
            value = _finite_number(getattr(self, field), field)
            if value < 0:
                raise ValueError(f"{field} must be >= 0")
            object.__setattr__(self, field, value)

    def to_dict(self) -> dict[str, object]:
        return {
            "max_source_bytes": self.max_source_bytes,
            "max_triangles": self.max_triangles,
            "weld_tolerance_mm": self.weld_tolerance_mm,
            "degenerate_area_epsilon_mm2": self.degenerate_area_epsilon_mm2,
            "zero_volume_epsilon_mm3": self.zero_volume_epsilon_mm3,
            "max_abs_coordinate_mm": self.max_abs_coordinate_mm,
        }

    @property
    def limits_sha256(self) -> str:
        return _canonical_sha256(self.to_dict())


@dataclass(frozen=True, slots=True)
class KernelBodyObservation:
    """Optional external CAD-kernel body count bound to the same STL source."""

    source_sha256: str
    evaluator_id: str
    status: str
    body_count: int | None
    evidence_sha256: str | None
    schema_version: str = KERNEL_BODY_OBSERVATION_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != KERNEL_BODY_OBSERVATION_VERSION:
            raise ValueError("unsupported kernel body observation version")
        object.__setattr__(self, "source_sha256", _sha256(self.source_sha256, "source_sha256"))
        object.__setattr__(self, "evaluator_id", _nonempty_string(self.evaluator_id, "evaluator_id"))
        if self.status not in {"completed", "inconclusive", "error"}:
            raise ValueError("kernel body status must be completed, inconclusive, or error")
        if self.status == "completed":
            if isinstance(self.body_count, bool) or not isinstance(self.body_count, int) or self.body_count < 0:
                raise ValueError("completed kernel body count must be a non-negative integer")
            object.__setattr__(self, "evidence_sha256", _sha256(self.evidence_sha256, "evidence_sha256"))
        else:
            if self.body_count is not None:
                raise ValueError("inconclusive/error kernel observation cannot assert a body count")
            if self.evidence_sha256 is not None:
                object.__setattr__(self, "evidence_sha256", _sha256(self.evidence_sha256, "evidence_sha256"))

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "source_sha256": self.source_sha256,
            "evaluator_id": self.evaluator_id,
            "status": self.status,
            "body_count": self.body_count,
            "evidence_sha256": self.evidence_sha256,
        }

    @property
    def observation_sha256(self) -> str:
        return _canonical_sha256(self.to_dict())


@dataclass(frozen=True, slots=True)
class StlTopologyReceipt:
    schema_version: str
    status: str
    source_sha256: str
    source_bytes: int
    limits_sha256: str
    stl_format: str | None
    source_triangle_count: int | None
    validated_triangle_count: int | None
    welded_vertex_count: int | None
    degenerate_triangle_count: int | None
    boundary_edge_count: int | None
    nonmanifold_edge_count: int | None
    inconsistent_winding_edge_count: int | None
    observed_shell_count: int | None
    expected_shell_count: int
    shell_signed_volumes_mm3: tuple[float, ...]
    bounds_min_mm: tuple[float, float, float] | None
    bounds_max_mm: tuple[float, float, float] | None
    expected_body_count: int | None
    observed_kernel_body_count: int | None
    kernel_status: str
    failure_reasons: tuple[str, ...]
    hold_reasons: tuple[str, ...]
    limitations: tuple[str, ...] = _STL_LIMITATIONS

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "source_sha256": self.source_sha256,
            "source_bytes": self.source_bytes,
            "limits_sha256": self.limits_sha256,
            "stl_format": self.stl_format,
            "source_triangle_count": self.source_triangle_count,
            "validated_triangle_count": self.validated_triangle_count,
            "welded_vertex_count": self.welded_vertex_count,
            "degenerate_triangle_count": self.degenerate_triangle_count,
            "boundary_edge_count": self.boundary_edge_count,
            "nonmanifold_edge_count": self.nonmanifold_edge_count,
            "inconsistent_winding_edge_count": self.inconsistent_winding_edge_count,
            "observed_shell_count": self.observed_shell_count,
            "expected_shell_count": self.expected_shell_count,
            "shell_signed_volumes_mm3": list(self.shell_signed_volumes_mm3),
            "bounds_min_mm": None if self.bounds_min_mm is None else list(self.bounds_min_mm),
            "bounds_max_mm": None if self.bounds_max_mm is None else list(self.bounds_max_mm),
            "expected_body_count": self.expected_body_count,
            "observed_kernel_body_count": self.observed_kernel_body_count,
            "kernel_status": self.kernel_status,
            "failure_reasons": list(self.failure_reasons),
            "hold_reasons": list(self.hold_reasons),
            "limitations": list(self.limitations),
        }

    @property
    def receipt_sha256(self) -> str:
        return _canonical_sha256(self.to_dict())


class _StlParseError(ValueError):
    def __init__(self, code: str, *, definite_failure: bool = False) -> None:
        self.code = code
        self.definite_failure = definite_failure
        super().__init__(code)


Triangle = tuple[
    tuple[float, float, float],
    tuple[float, float, float],
    tuple[float, float, float],
]


def _checked_float(token: object, code: str) -> float:
    try:
        value = float(token)
    except (TypeError, ValueError) as error:
        raise _StlParseError("malformed_numeric_token") from error
    if not math.isfinite(value):
        raise _StlParseError(code, definite_failure=True)
    return value


def _check_coordinate(value: float, limits: StlInspectionLimits) -> float:
    if abs(value) > limits.max_abs_coordinate_mm:
        raise _StlParseError("coordinate_safety_limit_exceeded")
    return value


def _parse_binary_stl(source: bytes, limits: StlInspectionLimits) -> list[Triangle]:
    if len(source) < 84:
        raise _StlParseError("truncated_binary_header")
    count = struct.unpack_from("<I", source, 80)[0]
    if count > limits.max_triangles:
        raise _StlParseError("triangle_limit_exceeded")
    expected = 84 + count * 50
    if len(source) != expected:
        raise _StlParseError("binary_size_mismatch")
    if count == 0:
        raise _StlParseError("empty_stl", definite_failure=True)
    triangles: list[Triangle] = []
    offset = 84
    for _ in range(count):
        values = struct.unpack_from("<12fH", source, offset)
        offset += 50
        if any(not math.isfinite(value) for value in values[:12]):
            raise _StlParseError("nonfinite_binary_float", definite_failure=True)
        vertices: list[tuple[float, float, float]] = []
        for start in (3, 6, 9):
            vertices.append(
                tuple(
                    _check_coordinate(float(values[index]), limits)
                    for index in range(start, start + 3)
                )
            )
        triangles.append((vertices[0], vertices[1], vertices[2]))
    return triangles


def _parse_ascii_stl(source: bytes, limits: StlInspectionLimits) -> list[Triangle]:
    try:
        text = source.decode("ascii")
    except UnicodeDecodeError as error:
        raise _StlParseError("ascii_decode_error") from error
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) < 2:
        raise _StlParseError("truncated_ascii_stl")
    first = lines[0].split(maxsplit=1)
    if first[0].lower() != "solid":
        raise _StlParseError("missing_ascii_solid")
    solid_name = first[1] if len(first) == 2 else ""
    triangles: list[Triangle] = []
    index = 1
    ended = False
    while index < len(lines):
        tokens = lines[index].split()
        if tokens and tokens[0].lower() == "endsolid":
            if index != len(lines) - 1:
                raise _StlParseError("ascii_trailing_content")
            end_name = " ".join(tokens[1:])
            if solid_name and end_name and end_name != solid_name:
                raise _StlParseError("ascii_solid_name_mismatch")
            ended = True
            break
        if len(tokens) != 5 or [token.lower() for token in tokens[:2]] != ["facet", "normal"]:
            raise _StlParseError("malformed_ascii_facet")
        for token in tokens[2:]:
            _checked_float(token, "nonfinite_ascii_normal")
        index += 1
        if index >= len(lines) or [token.lower() for token in lines[index].split()] != ["outer", "loop"]:
            raise _StlParseError("missing_ascii_outer_loop")
        index += 1
        vertices: list[tuple[float, float, float]] = []
        for _ in range(3):
            if index >= len(lines):
                raise _StlParseError("truncated_ascii_vertex")
            vertex_tokens = lines[index].split()
            if len(vertex_tokens) != 4 or vertex_tokens[0].lower() != "vertex":
                raise _StlParseError("malformed_ascii_vertex")
            vertex = tuple(
                _check_coordinate(
                    _checked_float(token, "nonfinite_ascii_coordinate"), limits
                )
                for token in vertex_tokens[1:]
            )
            vertices.append(vertex)
            index += 1
        if index >= len(lines) or lines[index].lower() != "endloop":
            raise _StlParseError("missing_ascii_endloop")
        index += 1
        if index >= len(lines) or lines[index].lower() != "endfacet":
            raise _StlParseError("missing_ascii_endfacet")
        index += 1
        triangles.append((vertices[0], vertices[1], vertices[2]))
        if len(triangles) > limits.max_triangles:
            raise _StlParseError("triangle_limit_exceeded")
    if not ended:
        raise _StlParseError("missing_ascii_endsolid")
    if not triangles:
        raise _StlParseError("empty_stl", definite_failure=True)
    return triangles


def _parse_stl(source: bytes, limits: StlInspectionLimits) -> tuple[str, list[Triangle]]:
    if len(source) >= 84:
        count = struct.unpack_from("<I", source, 80)[0]
        if 84 + count * 50 == len(source):
            return "binary", _parse_binary_stl(source, limits)
    if source.lstrip().lower().startswith(b"solid"):
        return "ascii", _parse_ascii_stl(source, limits)
    return "binary", _parse_binary_stl(source, limits)


class _UnionFind:
    def __init__(self, count: int) -> None:
        self.parent = list(range(count))

    def find(self, item: int) -> int:
        parent = self.parent
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    def union(self, left: int, right: int) -> None:
        root_left = self.find(left)
        root_right = self.find(right)
        if root_left != root_right:
            self.parent[root_right] = root_left


def _empty_stl_receipt(
    *,
    status: str,
    source_sha256: str,
    source_bytes: int,
    limits: StlInspectionLimits,
    stl_format: str | None,
    expected_shell_count: int,
    expected_body_count: int | None,
    failure_reasons: Sequence[str] = (),
    hold_reasons: Sequence[str] = (),
) -> StlTopologyReceipt:
    return StlTopologyReceipt(
        schema_version=STL_INSPECTION_RECEIPT_VERSION,
        status=status,
        source_sha256=source_sha256,
        source_bytes=source_bytes,
        limits_sha256=limits.limits_sha256,
        stl_format=stl_format,
        source_triangle_count=None,
        validated_triangle_count=None,
        welded_vertex_count=None,
        degenerate_triangle_count=None,
        boundary_edge_count=None,
        nonmanifold_edge_count=None,
        inconsistent_winding_edge_count=None,
        observed_shell_count=None,
        expected_shell_count=expected_shell_count,
        shell_signed_volumes_mm3=(),
        bounds_min_mm=None,
        bounds_max_mm=None,
        expected_body_count=expected_body_count,
        observed_kernel_body_count=None,
        kernel_status=(
            "not_evaluated" if expected_body_count is not None else "not_required"
        ),
        failure_reasons=tuple(failure_reasons),
        hold_reasons=tuple(hold_reasons),
    )


def inspect_stl_topology(
    source: bytes | bytearray | memoryview,
    *,
    expected_shell_count: int,
    expected_body_count: int | None = None,
    kernel_body_observation: KernelBodyObservation | None = None,
    expected_source_sha256: str | None = None,
    expected_source_bytes: int | None = None,
    limits: StlInspectionLimits | None = None,
) -> StlTopologyReceipt:
    """Inspect exact STL bytes and return a deterministic, fail-closed receipt.

    ``expected_shell_count`` is a topological expectation.  A CAD-kernel body
    count is a different claim: when ``expected_body_count`` is supplied, a
    completed :class:`KernelBodyObservation` bound to the same source hash is
    mandatory.  Missing or inconclusive kernel evidence holds the receipt.
    """

    if not isinstance(source, (bytes, bytearray, memoryview)):
        raise TypeError("source must be bytes-like")
    raw = bytes(source)
    limits = limits or StlInspectionLimits()
    if isinstance(expected_shell_count, bool) or not isinstance(expected_shell_count, int) or expected_shell_count < 1:
        raise ValueError("expected_shell_count must be a positive integer")
    if expected_body_count is not None and (
        isinstance(expected_body_count, bool)
        or not isinstance(expected_body_count, int)
        or expected_body_count < 1
    ):
        raise ValueError("expected_body_count must be a positive integer")
    if expected_source_sha256 is not None:
        expected_source_sha256 = _sha256(expected_source_sha256, "expected_source_sha256")
    if expected_source_bytes is not None and (
        isinstance(expected_source_bytes, bool)
        or not isinstance(expected_source_bytes, int)
        or expected_source_bytes < 0
    ):
        raise ValueError("expected_source_bytes must be a non-negative integer")
    actual_sha256 = hashlib.sha256(raw).hexdigest()
    hold_reasons: list[str] = []
    if expected_source_sha256 is not None and expected_source_sha256 != actual_sha256:
        hold_reasons.append("source_sha256_mismatch")
    if expected_source_bytes is not None and expected_source_bytes != len(raw):
        hold_reasons.append("source_byte_count_mismatch")
    if len(raw) > limits.max_source_bytes:
        hold_reasons.append("source_byte_limit_exceeded")
        return _empty_stl_receipt(
            status="held",
            source_sha256=actual_sha256,
            source_bytes=len(raw),
            limits=limits,
            stl_format=None,
            expected_shell_count=expected_shell_count,
            expected_body_count=expected_body_count,
            hold_reasons=hold_reasons,
        )

    stl_format: str | None = (
        "ascii" if raw.lstrip().lower().startswith(b"solid") else "binary"
    )
    if len(raw) >= 84:
        declared_count = struct.unpack_from("<I", raw, 80)[0]
        if 84 + declared_count * 50 == len(raw):
            stl_format = "binary"
    try:
        stl_format, triangles = _parse_stl(raw, limits)
    except _StlParseError as error:
        if error.definite_failure and not hold_reasons:
            return _empty_stl_receipt(
                status="failed",
                source_sha256=actual_sha256,
                source_bytes=len(raw),
                limits=limits,
                stl_format=stl_format,
                expected_shell_count=expected_shell_count,
                expected_body_count=expected_body_count,
                failure_reasons=(error.code,),
            )
        hold_reasons.append(error.code)
        return _empty_stl_receipt(
            status="held",
            source_sha256=actual_sha256,
            source_bytes=len(raw),
            limits=limits,
            stl_format=stl_format,
            expected_shell_count=expected_shell_count,
            expected_body_count=expected_body_count,
            hold_reasons=hold_reasons,
        )

    vertices: list[tuple[float, float, float]] = []
    vertex_by_key: dict[tuple[int, int, int], int] = {}
    faces: list[tuple[int, int, int]] = []
    degenerate = 0
    tolerance = limits.weld_tolerance_mm
    for triangle in triangles:
        face_indices: list[int] = []
        for vertex in triangle:
            try:
                scaled = tuple(component / tolerance for component in vertex)
                if any(not math.isfinite(component) for component in scaled):
                    raise OverflowError
                key = tuple(round(component) for component in scaled)
            except (OverflowError, ValueError):
                hold_reasons.append("weld_quantization_inconclusive")
                return _empty_stl_receipt(
                    status="held",
                    source_sha256=actual_sha256,
                    source_bytes=len(raw),
                    limits=limits,
                    stl_format=stl_format,
                    expected_shell_count=expected_shell_count,
                    expected_body_count=expected_body_count,
                    hold_reasons=hold_reasons,
                )
            index = vertex_by_key.get(key)
            if index is None:
                index = len(vertices)
                vertex_by_key[key] = index
                vertices.append(vertex)
            face_indices.append(index)
        a, b, c = face_indices
        if len({a, b, c}) != 3:
            degenerate += 1
            continue
        va, vb, vc = vertices[a], vertices[b], vertices[c]
        edge1 = (vb[0] - va[0], vb[1] - va[1], vb[2] - va[2])
        edge2 = (vc[0] - va[0], vc[1] - va[1], vc[2] - va[2])
        cross = (
            edge1[1] * edge2[2] - edge1[2] * edge2[1],
            edge1[2] * edge2[0] - edge1[0] * edge2[2],
            edge1[0] * edge2[1] - edge1[1] * edge2[0],
        )
        area = 0.5 * math.sqrt(sum(component * component for component in cross))
        if not math.isfinite(area) or area <= limits.degenerate_area_epsilon_mm2:
            degenerate += 1
            continue
        faces.append((a, b, c))

    failures: list[str] = []
    if degenerate:
        failures.append("degenerate_triangles")
    if not faces:
        failures.append("no_valid_triangles")
        status = "held" if hold_reasons else "failed"
        return StlTopologyReceipt(
            schema_version=STL_INSPECTION_RECEIPT_VERSION,
            status=status,
            source_sha256=actual_sha256,
            source_bytes=len(raw),
            limits_sha256=limits.limits_sha256,
            stl_format=stl_format,
            source_triangle_count=len(triangles),
            validated_triangle_count=0,
            welded_vertex_count=len(vertices),
            degenerate_triangle_count=degenerate,
            boundary_edge_count=None,
            nonmanifold_edge_count=None,
            inconsistent_winding_edge_count=None,
            observed_shell_count=0,
            expected_shell_count=expected_shell_count,
            shell_signed_volumes_mm3=(),
            bounds_min_mm=None,
            bounds_max_mm=None,
            expected_body_count=expected_body_count,
            observed_kernel_body_count=None,
            kernel_status=(
                "not_evaluated" if expected_body_count is not None else "not_required"
            ),
            failure_reasons=tuple(failures),
            hold_reasons=tuple(hold_reasons),
        )

    union = _UnionFind(len(faces))
    edge_data: dict[tuple[int, int], list[int]] = {}
    for face_index, (a, b, c) in enumerate(faces):
        for left, right in ((a, b), (b, c), (c, a)):
            key = (left, right) if left < right else (right, left)
            direction = 1 if left < right else -1
            existing = edge_data.get(key)
            if existing is None:
                edge_data[key] = [1, direction, face_index]
            else:
                existing[0] += 1
                existing[1] += direction
                union.union(existing[2], face_index)
    boundary = sum(1 for count, _, _ in edge_data.values() if count == 1)
    nonmanifold = sum(1 for count, _, _ in edge_data.values() if count > 2)
    inconsistent = sum(
        1 for count, direction, _ in edge_data.values() if count == 2 and direction != 0
    )
    if boundary:
        failures.append("boundary_edges")
    if nonmanifold:
        failures.append("nonmanifold_edges")
    if inconsistent:
        failures.append("inconsistent_winding")

    shell_faces: dict[int, list[tuple[int, int, int]]] = {}
    for face_index, face in enumerate(faces):
        shell_faces.setdefault(union.find(face_index), []).append(face)
    observed_shell_count = len(shell_faces)
    if observed_shell_count != expected_shell_count:
        failures.append("unexpected_shell_count")

    shell_volumes: list[float] = []
    for root in sorted(shell_faces):
        shell = shell_faces[root]
        reference = vertices[shell[0][0]]
        terms: list[float] = []
        for a, b, c in shell:
            va = tuple(vertices[a][axis] - reference[axis] for axis in range(3))
            vb = tuple(vertices[b][axis] - reference[axis] for axis in range(3))
            vc = tuple(vertices[c][axis] - reference[axis] for axis in range(3))
            cross = (
                vb[1] * vc[2] - vb[2] * vc[1],
                vb[2] * vc[0] - vb[0] * vc[2],
                vb[0] * vc[1] - vb[1] * vc[0],
            )
            terms.append((va[0] * cross[0] + va[1] * cross[1] + va[2] * cross[2]) / 6.0)
        try:
            volume = math.fsum(terms)
        except (OverflowError, ValueError):
            volume = math.nan
        shell_volumes.append(volume)
        if not math.isfinite(volume) or abs(volume) <= limits.zero_volume_epsilon_mm3:
            failures.append("zero_or_nonfinite_shell_volume")
        elif volume < 0:
            failures.append("inward_shell_winding")

    xs = [vertex[0] for vertex in vertices]
    ys = [vertex[1] for vertex in vertices]
    zs = [vertex[2] for vertex in vertices]
    bounds_min = (min(xs), min(ys), min(zs))
    bounds_max = (max(xs), max(ys), max(zs))

    kernel_status = "not_required"
    observed_body_count: int | None = None
    if expected_body_count is not None:
        if kernel_body_observation is None:
            kernel_status = "not_evaluated"
            hold_reasons.append("kernel_body_count_not_evaluated")
        elif kernel_body_observation.source_sha256 != actual_sha256:
            kernel_status = "source_mismatch"
            hold_reasons.append("kernel_body_source_sha256_mismatch")
        elif kernel_body_observation.status != "completed":
            kernel_status = kernel_body_observation.status
            hold_reasons.append(f"kernel_body_{kernel_body_observation.status}")
        else:
            kernel_status = "completed"
            observed_body_count = kernel_body_observation.body_count
            if observed_body_count != expected_body_count:
                failures.append("unexpected_kernel_body_count")
    elif kernel_body_observation is not None:
        kernel_status = kernel_body_observation.status
        if kernel_body_observation.source_sha256 != actual_sha256:
            hold_reasons.append("kernel_body_source_sha256_mismatch")

    failures = list(dict.fromkeys(failures))
    hold_reasons = list(dict.fromkeys(hold_reasons))
    status = "held" if hold_reasons else ("failed" if failures else "passed")
    return StlTopologyReceipt(
        schema_version=STL_INSPECTION_RECEIPT_VERSION,
        status=status,
        source_sha256=actual_sha256,
        source_bytes=len(raw),
        limits_sha256=limits.limits_sha256,
        stl_format=stl_format,
        source_triangle_count=len(triangles),
        validated_triangle_count=len(faces),
        welded_vertex_count=len(vertices),
        degenerate_triangle_count=degenerate,
        boundary_edge_count=boundary,
        nonmanifold_edge_count=nonmanifold,
        inconsistent_winding_edge_count=inconsistent,
        observed_shell_count=observed_shell_count,
        expected_shell_count=expected_shell_count,
        shell_signed_volumes_mm3=tuple(shell_volumes),
        bounds_min_mm=bounds_min,
        bounds_max_mm=bounds_max,
        expected_body_count=expected_body_count,
        observed_kernel_body_count=observed_body_count,
        kernel_status=kernel_status,
        failure_reasons=tuple(failures),
        hold_reasons=tuple(hold_reasons),
    )


_MOTION_CHECKS = frozenset(
    {
        "linear_motion_collision",
        "rotation_motion_collision",
        "clear_path_proxy",
        "assembly_sequence",
    }
)
_MOTION_MAX_STEPS = 10_000
_MOTION_MAX_SEQUENCE_ITEMS = 256
_MOTION_MAX_SEQUENCE_DEPTH = 8


def _motion_vector(value: object, field: str) -> tuple[float, float, float]:
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise ValueError(f"{field} must be a three-number vector")
    return tuple(_finite_number(component, field) for component in value)  # type: ignore[return-value]


def _motion_parts(value: object, field: str) -> tuple[str, ...]:
    values: Sequence[object]
    if isinstance(value, str):
        values = (value,)
    elif isinstance(value, (list, tuple)):
        values = value
    else:
        raise ValueError(f"{field} must name one or more parts")
    if not values or len(values) > _MOTION_MAX_SEQUENCE_ITEMS:
        raise ValueError(f"{field} must name 1..{_MOTION_MAX_SEQUENCE_ITEMS} parts")
    names = tuple(_nonempty_string(item, field) for item in values)
    if len(set(names)) != len(names):
        raise ValueError(f"{field} must not contain duplicate parts")
    return names


def _motion_steps(value: object, field: str = "inputs.steps") -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= _MOTION_MAX_STEPS:
        raise ValueError(f"{field} must be an integer from 1 to {_MOTION_MAX_STEPS}")
    return value


@dataclass(frozen=True, slots=True, init=False)
class MotionCondition:
    """A canonical, hash-bound version of a Peter-style motion condition."""

    schema_version: str
    condition_id: str
    check: str
    expect: str
    description: str
    inputs_json: str
    thresholds_json: str

    def __init__(
        self,
        *,
        condition_id: str,
        check: str,
        expect: str,
        inputs: Mapping[str, Any],
        thresholds: Mapping[str, Any] | None = None,
        description: str = "",
        schema_version: str = MOTION_CONDITION_VERSION,
        _depth: int = 0,
    ) -> None:
        if schema_version != MOTION_CONDITION_VERSION:
            raise ValueError(f"unsupported motion condition version {schema_version!r}")
        condition_id = _nonempty_string(condition_id, "condition id")
        if check not in _MOTION_CHECKS:
            raise ValueError(f"unsupported motion check {check!r}")
        if expect not in {"clear", "blocked"}:
            raise ValueError("motion expect must be exactly 'clear' or 'blocked'")
        if not isinstance(description, str):
            raise TypeError("motion description must be a string")
        if not isinstance(inputs, Mapping):
            raise TypeError("motion inputs must be an object")
        if thresholds is not None and not isinstance(thresholds, Mapping):
            raise TypeError("motion thresholds must be an object")
        copied_inputs = _json_copy(inputs, "motion inputs")
        copied_thresholds = _json_copy(thresholds or {}, "motion thresholds")
        self._validate_inputs(check, copied_inputs, condition_id, _depth)
        unknown_thresholds = sorted(set(copied_thresholds) - {"maxOverlapMm3"})
        if unknown_thresholds:
            raise ValueError(
                f"unknown motion threshold fields: {', '.join(unknown_thresholds)}"
            )
        overlap = copied_thresholds.get("maxOverlapMm3")
        if check != "assembly_sequence" and overlap is None:
            raise ValueError("motion condition requires thresholds.maxOverlapMm3")
        if overlap is not None and _finite_number(overlap, "thresholds.maxOverlapMm3") < 0:
            raise ValueError("thresholds.maxOverlapMm3 must be >= 0")
        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "condition_id", condition_id)
        object.__setattr__(self, "check", check)
        object.__setattr__(self, "expect", expect)
        object.__setattr__(self, "description", description)
        object.__setattr__(self, "inputs_json", _canonical_json(copied_inputs))
        object.__setattr__(self, "thresholds_json", _canonical_json(copied_thresholds))

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any], *, _depth: int = 0) -> "MotionCondition":
        if not isinstance(raw, Mapping):
            raise TypeError("motion condition must be an object")
        allowed = {
            "schema_version",
            "id",
            "check",
            "expect",
            "description",
            "inputs",
            "thresholds",
        }
        unknown = sorted(set(raw) - allowed)
        if unknown:
            raise ValueError(f"unknown motion condition fields: {', '.join(unknown)}")
        if "id" not in raw:
            raise ValueError("motion condition requires an explicit id")
        if "expect" not in raw:
            raise ValueError("motion condition requires an explicit expect")
        return cls(
            schema_version=raw.get("schema_version", MOTION_CONDITION_VERSION),
            condition_id=raw["id"],
            check=raw.get("check"),
            expect=raw["expect"],
            description=raw.get("description", ""),
            inputs=raw.get("inputs", {}),
            thresholds=raw.get("thresholds", {}),
            _depth=_depth,
        )

    @staticmethod
    def _validate_inputs(check: str, inputs: dict[str, Any], ident: str, depth: int) -> None:
        if depth > _MOTION_MAX_SEQUENCE_DEPTH:
            raise ValueError("assembly_sequence exceeds the nesting limit")
        if check == "linear_motion_collision":
            allowed = {
                "moving_part",
                "obstacle_parts",
                "translation",
                "steps",
                "allow_seated_contact",
            }
            _nonempty_string(inputs.get("moving_part"), "inputs.moving_part")
            _motion_parts(inputs.get("obstacle_parts"), "inputs.obstacle_parts")
            translation = _motion_vector(inputs.get("translation"), "inputs.translation")
            if not any(translation):
                raise ValueError("inputs.translation must not be the zero vector")
            _motion_steps(inputs.get("steps"))
        elif check == "rotation_motion_collision":
            allowed = {
                "moving_part",
                "obstacle_parts",
                "axis_point",
                "axis_direction",
                "start_deg",
                "end_deg",
                "steps",
                "allow_seated_contact",
            }
            _nonempty_string(inputs.get("moving_part"), "inputs.moving_part")
            _motion_parts(inputs.get("obstacle_parts"), "inputs.obstacle_parts")
            _motion_vector(inputs.get("axis_point"), "inputs.axis_point")
            direction = _motion_vector(inputs.get("axis_direction"), "inputs.axis_direction")
            if not any(direction):
                raise ValueError("inputs.axis_direction must not be the zero vector")
            start = _finite_number(inputs.get("start_deg"), "inputs.start_deg")
            end = _finite_number(inputs.get("end_deg"), "inputs.end_deg")
            if start == end:
                raise ValueError("rotation start_deg and end_deg must differ")
            _motion_steps(inputs.get("steps"))
        elif check == "clear_path_proxy":
            allowed = {
                "start",
                "end",
                "radius",
                "obstacle_parts",
                "allow_seated_contact",
            }
            start = _motion_vector(inputs.get("start"), "inputs.start")
            end = _motion_vector(inputs.get("end"), "inputs.end")
            if start == end:
                raise ValueError("clear-path start and end must differ")
            _positive_number(inputs.get("radius"), "inputs.radius")
            _motion_parts(inputs.get("obstacle_parts"), "inputs.obstacle_parts")
        else:
            allowed = {"steps"}
            steps = inputs.get("steps")
            if not isinstance(steps, list) or not 1 <= len(steps) <= _MOTION_MAX_SEQUENCE_ITEMS:
                raise ValueError("assembly_sequence inputs.steps must be a bounded non-empty list")
            normalized: list[dict[str, object]] = []
            for index, step in enumerate(steps):
                if not isinstance(step, Mapping):
                    raise TypeError("each assembly_sequence step must be an object")
                child_raw = dict(step)
                child_raw.setdefault("id", f"{ident}.{index}")
                child = MotionCondition.from_mapping(child_raw, _depth=depth + 1)
                normalized.append(child.to_dict())
            inputs["steps"] = normalized
        unknown = sorted(set(inputs) - allowed)
        if unknown:
            raise ValueError(f"unknown {check} input fields: {', '.join(unknown)}")
        if "allow_seated_contact" in inputs and not isinstance(inputs["allow_seated_contact"], bool):
            raise TypeError("inputs.allow_seated_contact must be a boolean")

    @property
    def inputs(self) -> dict[str, Any]:
        return json.loads(self.inputs_json)

    @property
    def thresholds(self) -> dict[str, Any]:
        return json.loads(self.thresholds_json)

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "id": self.condition_id,
            "check": self.check,
            "expect": self.expect,
            "description": self.description,
            "inputs": self.inputs,
            "thresholds": self.thresholds,
        }

    @property
    def condition_sha256(self) -> str:
        return _canonical_sha256(self.to_dict())


@dataclass(frozen=True, slots=True)
class MotionEvaluatorOutcome:
    """A primitive kernel observation, before applying the expectation."""

    condition_sha256: str
    evaluator_id: str
    status: str
    clear: bool | None
    evidence_sha256: str | None
    detail_code: str
    schema_version: str = MOTION_OUTCOME_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != MOTION_OUTCOME_VERSION:
            raise ValueError("unsupported motion outcome version")
        object.__setattr__(self, "condition_sha256", _sha256(self.condition_sha256, "condition_sha256"))
        object.__setattr__(self, "evaluator_id", _nonempty_string(self.evaluator_id, "evaluator_id"))
        object.__setattr__(self, "detail_code", _nonempty_string(self.detail_code, "detail_code"))
        if self.status not in {"completed", "inconclusive", "error"}:
            raise ValueError("motion outcome status must be completed, inconclusive, or error")
        if self.status == "completed":
            if type(self.clear) is not bool:
                raise TypeError("completed motion outcome clear must be an exact boolean")
            object.__setattr__(self, "evidence_sha256", _sha256(self.evidence_sha256, "evidence_sha256"))
        else:
            if self.clear is not None:
                raise ValueError("inconclusive/error motion outcome cannot assert clear")
            if self.evidence_sha256 is not None:
                object.__setattr__(self, "evidence_sha256", _sha256(self.evidence_sha256, "evidence_sha256"))

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "MotionEvaluatorOutcome":
        if not isinstance(raw, Mapping):
            raise TypeError("motion evaluator outcome must be an object")
        allowed = {
            "schema_version",
            "condition_sha256",
            "evaluator_id",
            "status",
            "clear",
            "evidence_sha256",
            "detail_code",
        }
        unknown = sorted(set(raw) - allowed)
        if unknown:
            raise ValueError(f"unknown motion outcome fields: {', '.join(unknown)}")
        return cls(
            schema_version=raw.get("schema_version", MOTION_OUTCOME_VERSION),
            condition_sha256=raw.get("condition_sha256"),
            evaluator_id=raw.get("evaluator_id"),
            status=raw.get("status"),
            clear=raw.get("clear"),
            evidence_sha256=raw.get("evidence_sha256"),
            detail_code=raw.get("detail_code", "unspecified"),
        )


@dataclass(frozen=True, slots=True)
class MotionValidationReceipt:
    schema_version: str
    status: str
    condition_id: str
    condition_sha256: str
    check: str
    expect: str
    evaluator_id: str | None
    evaluator_status: str
    observed_clear: bool | None
    evidence_sha256: str | None
    detail_code: str | None
    reasons: tuple[str, ...]
    limitations: tuple[str, ...] = _MOTION_LIMITATIONS

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "condition_id": self.condition_id,
            "condition_sha256": self.condition_sha256,
            "check": self.check,
            "expect": self.expect,
            "evaluator_id": self.evaluator_id,
            "evaluator_status": self.evaluator_status,
            "observed_clear": self.observed_clear,
            "evidence_sha256": self.evidence_sha256,
            "detail_code": self.detail_code,
            "reasons": list(self.reasons),
            "limitations": list(self.limitations),
        }

    @property
    def receipt_sha256(self) -> str:
        return _canonical_sha256(self.to_dict())


def _held_motion_receipt(
    condition: MotionCondition,
    reason: str,
    *,
    evaluator_id: str | None = None,
    evaluator_status: str = "error",
    evidence_sha256: str | None = None,
    detail_code: str | None = None,
) -> MotionValidationReceipt:
    return MotionValidationReceipt(
        schema_version=MOTION_RECEIPT_VERSION,
        status="held",
        condition_id=condition.condition_id,
        condition_sha256=condition.condition_sha256,
        check=condition.check,
        expect=condition.expect,
        evaluator_id=evaluator_id,
        evaluator_status=evaluator_status,
        observed_clear=None,
        evidence_sha256=evidence_sha256,
        detail_code=detail_code,
        reasons=(reason,),
    )


def validate_motion_outcome(
    condition: MotionCondition, outcome: MotionEvaluatorOutcome
) -> MotionValidationReceipt:
    """Apply an expectation only to a conclusive, bound, exact boolean."""

    if outcome.condition_sha256 != condition.condition_sha256:
        return _held_motion_receipt(
            condition,
            "condition_sha256_mismatch",
            evaluator_id=outcome.evaluator_id,
            evaluator_status=outcome.status,
            evidence_sha256=outcome.evidence_sha256,
            detail_code=outcome.detail_code,
        )
    if outcome.status != "completed":
        return _held_motion_receipt(
            condition,
            f"evaluator_{outcome.status}",
            evaluator_id=outcome.evaluator_id,
            evaluator_status=outcome.status,
            evidence_sha256=outcome.evidence_sha256,
            detail_code=outcome.detail_code,
        )
    expected_clear = condition.expect == "clear"
    matched = outcome.clear is expected_clear
    return MotionValidationReceipt(
        schema_version=MOTION_RECEIPT_VERSION,
        status="passed" if matched else "failed",
        condition_id=condition.condition_id,
        condition_sha256=condition.condition_sha256,
        check=condition.check,
        expect=condition.expect,
        evaluator_id=outcome.evaluator_id,
        evaluator_status=outcome.status,
        observed_clear=outcome.clear,
        evidence_sha256=outcome.evidence_sha256,
        detail_code=outcome.detail_code,
        reasons=() if matched else ("motion_expectation_not_met",),
    )


def evaluate_motion_condition(
    condition: MotionCondition,
    evaluator: Callable[[MotionCondition], MotionEvaluatorOutcome | Mapping[str, Any]],
) -> MotionValidationReceipt:
    """Run an evaluator without allowing its exception/malformed result to pass."""

    try:
        raw = evaluator(condition)
    except Exception as error:  # evaluator/kernel failures are evidence, not control flow
        return _held_motion_receipt(
            condition, f"evaluator_exception:{type(error).__name__}"
        )
    try:
        outcome = raw if isinstance(raw, MotionEvaluatorOutcome) else MotionEvaluatorOutcome.from_mapping(raw)
    except Exception:  # malformed/lazy mappings are evaluator failures too
        return _held_motion_receipt(condition, "malformed_evaluator_outcome")
    return validate_motion_outcome(condition, outcome)


__all__ = [
    "ASSEMBLED_FIT_RECEIPT_VERSION",
    "CALIBRATION_PROFILE_VERSION",
    "KERNEL_BODY_OBSERVATION_VERSION",
    "MOTION_CONDITION_VERSION",
    "MOTION_OUTCOME_VERSION",
    "MOTION_RECEIPT_VERSION",
    "PRINT_IN_PLACE_RECEIPT_VERSION",
    "STL_INSPECTION_RECEIPT_VERSION",
    "UPSTREAM_MIT_NOTICE",
    "UPSTREAM_SOURCE_COMMIT",
    "UPSTREAM_SOURCE_PATHS",
    "AssembledFitCalibration",
    "AssembledFitReceipt",
    "KernelBodyObservation",
    "MotionCondition",
    "MotionEvaluatorOutcome",
    "MotionValidationReceipt",
    "PrintInPlaceFitCalibration",
    "PrintInPlaceFitReceipt",
    "PrinterCalibrationProfile",
    "PrinterTarget",
    "ProfileBindingReceipt",
    "ProfileSelfCheckReceipt",
    "StlInspectionLimits",
    "StlTopologyReceipt",
    "derive_assembled_fit",
    "derive_print_in_place_fit",
    "evaluate_motion_condition",
    "inspect_stl_topology",
    "self_check_calibration_profile",
    "validate_motion_outcome",
    "validate_profile_binding",
]
