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
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from inventor_workshop.cad.mesh import (
    KERNEL_BODY_OBSERVATION_VERSION,
    STL_INSPECTION_RECEIPT_VERSION,
    KernelBodyObservation,
    StlInspectionLimits,
    StlPathInspectionError,
    StlTopologyReceipt,
    fits_bed_envelope,
    inspect_stl_path,
    inspect_stl_topology,
)


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
    "StlPathInspectionError",
    "StlTopologyReceipt",
    "derive_assembled_fit",
    "derive_print_in_place_fit",
    "evaluate_motion_condition",
    "fits_bed_envelope",
    "inspect_stl_path",
    "inspect_stl_topology",
    "self_check_calibration_profile",
    "validate_motion_outcome",
    "validate_profile_binding",
]
