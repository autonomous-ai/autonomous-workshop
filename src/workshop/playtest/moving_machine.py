"""Playtest-owned deterministic verification for a narrow moving-machine lane.

The shared primitive CAD generator can currently represent rigid boxes and
cylinders.  This module verifies the useful subset of moving machines that can
be expressed honestly with those parts: one rigid body rotating about its own
assembly-Z axis, with explicit supports, obstacles, tolerance interfaces, load
paths, and failure-mode bindings.

The binding is a sealed Make artifact.  It is deliberately structured instead
of inferred from Invent prose during Playtest.  Every Invent tolerance, load,
and failure record must be mapped exactly once to real part identifiers.  A
mechanism outside this subset raises :class:`WaitingFor`; it never becomes a
model-authored pass.

Passing evidence is digital only.  The verifier combines the locked CAD
kernel's rigid-body sweeps with a conservative continuous swept envelope and
bounded primitive stress calculations.  It does not prove physical fit,
friction, retention, wear rate, durability, manufacture, or safety.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

from workshop.errors import ContractError
from workshop.make import (
    MOVING_MACHINE_BINDING_KIND,
    MOVING_MACHINE_BINDING_VERSION,
    canonical_cad_project_sources,
    locked_cad_project_verifier,
    moving_machine_parts,
    validate_moving_machine_binding,
    validate_moving_machine_lane_contract,
    workshop_pinned_wear_model,
)
from workshop.outcomes import Need, WaitingFor
from workshop.playtest.release import CapabilityReleaseProof, ReleaseProofSource


MOVING_MACHINE_CHECKER_VERSION = "1.0.0"

_DIMENSION_TOLERANCE_MM = 0.2
_MAX_OVERLAP_MM3 = 0.001
_PLA_ALLOWABLE_COMPRESSION_MPA = 5.0
_PLA_ALLOWABLE_SHEAR_MPA = 3.0
_EXECUTABLE_SUFFIXES = frozenset(
    (".py", ".pyc", ".pyo", ".so", ".dylib", ".pyd", ".pth")
)
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_SUPPORTED_LOAD_MODES = frozenset(("bulk-compression", "direct-shear"))
_PINNED_WEAR_MODEL = workshop_pinned_wear_model()
_NOT_PROVEN = (
    "physical fit, retention, friction, press force, or printer accuracy",
    "physical wear rate, fatigue, impact resistance, or durability",
    "spring, gear-tooth, compliant-joint, or multi-link dynamics",
    "material variability, physical misuse, or product safety",
    "human play or customer experience",
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
        raise ContractError("moving-machine evidence must be finite JSON") from exc


def _json_sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _document_bytes(value: Mapping[str, Any]) -> bytes:
    try:
        payload = (
            json.dumps(
                dict(value),
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ContractError("moving-machine receipt must be finite JSON") from exc
    if not payload or len(payload) > 1024 * 1024:
        raise ContractError("moving-machine receipt is empty or oversized")
    return payload


def _wait(capability: str, reason: str, instructions: str) -> WaitingFor:
    return WaitingFor(Need("playtest", capability, reason, instructions))


def _require_sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise ContractError("%s must be a lowercase SHA-256" % label)
    return value


def _safe_product_file(
    root: Path, inventory: Mapping[str, str], relative: str
) -> Tuple[Path, bytes, str]:
    digest = inventory.get(relative)
    _require_sha256(digest, "%s inventory digest" % relative)
    path = root / relative
    try:
        resolved = path.resolve(strict=True)
        resolved.relative_to(root.resolve(strict=True))
        if path.is_symlink() or not resolved.is_file():
            raise OSError("not a regular file")
        payload = resolved.read_bytes()
    except (OSError, ValueError) as exc:
        raise ContractError("sealed moving-machine source is missing or unsafe: %s" % relative) from exc
    if not payload or hashlib.sha256(payload).hexdigest() != digest:
        raise ContractError("sealed moving-machine source bytes changed: %s" % relative)
    return resolved, payload, digest


def _sealed_json(root: Path, inventory: Mapping[str, str], relative: str) -> Tuple[Mapping[str, Any], str]:
    unused_path, payload, digest = _safe_product_file(root, inventory, relative)
    del unused_path
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError("sealed moving-machine JSON is invalid: %s" % relative) from exc
    if not isinstance(value, Mapping):
        raise ContractError("sealed moving-machine JSON is not an object: %s" % relative)
    return value, digest





def _z_bounds(part: Mapping[str, Any]) -> Tuple[float, float]:
    center = part["assembly_center_mm"]
    center_z = float(center["z"])
    half_z = float(part["size_mm"]["z"]) / 2.0
    return center_z - half_z, center_z + half_z


def _moving_sweep_radius(part: Mapping[str, Any]) -> float:
    size = part["size_mm"]
    if part["shape"] == "cylinder":
        return float(size["x"]) / 2.0
    return math.hypot(float(size["x"]) / 2.0, float(size["y"]) / 2.0)


def _point_to_footprint_distance(
    point_xy: Sequence[float], part: Mapping[str, Any]
) -> float:
    center = part["assembly_center_mm"]
    dx = float(point_xy[0]) - float(center["x"])
    dy = float(point_xy[1]) - float(center["y"])
    size = part["size_mm"]
    if part["shape"] == "cylinder":
        return max(0.0, math.hypot(dx, dy) - float(size["x"]) / 2.0)
    angle = math.radians(float(part["assembly_rotation_deg"]))
    local_x = math.cos(angle) * dx + math.sin(angle) * dy
    local_y = -math.sin(angle) * dx + math.cos(angle) * dy
    outside_x = max(0.0, abs(local_x) - float(size["x"]) / 2.0)
    outside_y = max(0.0, abs(local_y) - float(size["y"]) / 2.0)
    return math.hypot(outside_x, outside_y)


def _continuous_clearance(
    moving: Mapping[str, Any], stationary: Mapping[str, Any]
) -> float:
    """Conservative all-angle separation of a centered Z-axis rigid sweep."""

    center = moving["assembly_center_mm"]
    radial = max(
        0.0,
        _point_to_footprint_distance((float(center["x"]), float(center["y"])), stationary)
        - _moving_sweep_radius(moving),
    )
    moving_z = _z_bounds(moving)
    stationary_z = _z_bounds(stationary)
    z_gap = max(
        0.0,
        moving_z[0] - stationary_z[1],
        stationary_z[0] - moving_z[1],
    )
    return math.hypot(radial, z_gap)


def _cross_section_mm2(part: Mapping[str, Any]) -> float:
    size = part["size_mm"]
    if part["shape"] == "cylinder":
        radius = float(size["x"]) / 2.0
        return math.pi * radius * radius
    return float(size["x"]) * float(size["y"])


def _motion_manifest(
    parts: Mapping[str, Mapping[str, Any]], binding: Mapping[str, Any]
) -> Mapping[str, Any]:
    joint = binding["joint"]
    moving_id = joint["moving_part_id"]
    moving_z = _z_bounds(parts[moving_id])
    maximum_z = max(_z_bounds(part)[1] for part in parts.values())
    travel = max(20.0, maximum_z - moving_z[0] + 10.0)
    common = {
        "moving_part": moving_id,
        "obstacle_parts": list(joint["support_part_ids"] + joint["obstacle_part_ids"]),
        "allow_seated_contact": True,
    }
    rotation = {
        **common,
        "axis_point": list(joint["axis_point_mm"]),
        "axis_direction": list(joint["axis_direction"]),
        "steps": joint["steps"],
    }
    return {
        "assembly": "product.step.py",
        "conditions": [
            {
                "id": "moving-machine-assembly-path",
                "check": "linear_motion_collision",
                "expect": "clear",
                "description": "Rigid upward disassembly path; reverse is the bounded assembly path.",
                "inputs": {**common, "translation": [0.0, 0.0, travel], "steps": 12},
                "thresholds": {"maxOverlapMm3": _MAX_OVERLAP_MM3},
            },
            {
                "id": "moving-machine-forward-sweep",
                "check": "rotation_motion_collision",
                "expect": "clear",
                "description": "Exact B-rep sampled through the declared forward rotary motion.",
                "inputs": {
                    **rotation,
                    "start_deg": joint["start_deg"],
                    "end_deg": joint["end_deg"],
                },
                "thresholds": {"maxOverlapMm3": _MAX_OVERLAP_MM3},
            },
            {
                "id": "moving-machine-reverse-sweep",
                "check": "rotation_motion_collision",
                "expect": "clear",
                "description": "Exact B-rep sampled through the reverse-motion misuse case.",
                "inputs": {
                    **rotation,
                    "start_deg": joint["start_deg"],
                    "end_deg": -float(joint["end_deg"]),
                },
                "thresholds": {"maxOverlapMm3": _MAX_OVERLAP_MM3},
            },
        ],
    }


def _copy_locked_cad(
    root: Path,
    inventory: Mapping[str, str],
    action: Mapping[str, Any],
    destination: Path,
) -> None:
    expected_sources = canonical_cad_project_sources(action)
    cad_root = root / "cad"
    if cad_root.is_symlink() or not cad_root.is_dir():
        raise ContractError("sealed moving-machine CAD root is missing or unsafe")
    executable = set()
    try:
        candidates = tuple(cad_root.rglob("*"))
    except OSError as exc:
        raise ContractError("sealed moving-machine CAD inventory cannot be inspected") from exc
    for candidate in candidates:
        if candidate.is_symlink():
            raise ContractError("sealed moving-machine CAD inventory contains a symlink")
        if candidate.is_file() and candidate.suffix.casefold() in _EXECUTABLE_SUFFIXES:
            executable.add(candidate.relative_to(cad_root).as_posix())
    if executable != set(expected_sources):
        raise ContractError("sealed moving-machine executable CAD differs from the locked Workshop template")
    for relative, source in expected_sources.items():
        unused_path, payload, unused_digest = _safe_product_file(
            root, inventory, "cad/" + relative
        )
        del unused_path, unused_digest
        if payload != source.encode("utf-8"):
            raise ContractError("sealed moving-machine CAD source differs from the locked Workshop template")

    for relative in sorted(path for path in inventory if path.startswith("cad/")):
        unused_path, payload, unused_digest = _safe_product_file(root, inventory, relative)
        del unused_path, unused_digest
        target = destination / Path(relative).relative_to("cad")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)


def _load_cases(
    parts: Mapping[str, Mapping[str, Any]],
    contract: Mapping[str, Any],
    binding: Mapping[str, Any],
) -> Tuple[Mapping[str, Any], ...]:
    rows = []
    for bound in binding["load_bindings"]:
        declared = contract["load_assumptions"][bound["contract_index"]]
        loaded = parts[bound["loaded_part_id"]]
        area = _cross_section_mm2(loaded)
        design_force = float(declared["force_n"]) * float(declared["safety_factor"])
        stress = design_force / area
        for mode in bound["verification_modes"]:
            allowable = (
                _PLA_ALLOWABLE_COMPRESSION_MPA
                if mode == "bulk-compression"
                else _PLA_ALLOWABLE_SHEAR_MPA
            )
            rows.append(
                {
                    "contract_index": bound["contract_index"],
                    "case": declared["case"],
                    "loaded_part_id": bound["loaded_part_id"],
                    "support_part_ids": list(bound["support_part_ids"]),
                    "kind": mode,
                    "declared_force_n": declared["force_n"],
                    "declared_safety_factor": declared["safety_factor"],
                    "design_force_n": round(design_force, 9),
                    "section_axis": "z",
                    "cross_section_mm2": round(area, 9),
                    "calculated_stress_mpa": round(stress, 12),
                    "digital_allowable_mpa": allowable,
                    "passed": stress <= allowable,
                }
            )
    return tuple(rows)


def _clearance_cases(
    parts: Mapping[str, Mapping[str, Any]],
    action: Mapping[str, Any],
    contract: Mapping[str, Any],
    binding: Mapping[str, Any],
) -> Tuple[Mapping[str, Any], ...]:
    moving_id = binding["joint"]["moving_part_id"]
    moving = parts[moving_id]
    declared_minimum = float(action["motion_spec"]["minimum_aabb_clearance_mm"])
    rows = []
    for bound in binding["tolerance_bindings"]:
        declared = contract["tolerances_mm"][bound["contract_index"]]
        contract_minimum = (
            float(declared["nominal_clearance_mm"])
            + float(declared["tolerance_mm"])
            + 2.0 * _DIMENSION_TOLERANCE_MM
        )
        required = max(declared_minimum, contract_minimum)
        for stationary_id in bound["stationary_part_ids"]:
            measured = _continuous_clearance(moving, parts[stationary_id])
            rows.append(
                {
                    "contract_index": bound["contract_index"],
                    "interface": declared["interface"],
                    "moving_part_id": moving_id,
                    "stationary_part_id": stationary_id,
                    "verification": "continuous-swept-envelope",
                    "declared_nominal_clearance_mm": declared["nominal_clearance_mm"],
                    "declared_tolerance_mm": declared["tolerance_mm"],
                    "workshop_dimension_tolerance_mm_per_part": _DIMENSION_TOLERANCE_MM,
                    "make_minimum_clearance_mm": declared_minimum,
                    "required_clearance_mm": round(required, 9),
                    "conservative_continuous_clearance_mm": round(measured, 9),
                    "passed": measured >= required,
                }
            )
    return tuple(rows)


def _wear_cases(
    clearances: Sequence[Mapping[str, Any]], binding: Mapping[str, Any]
) -> Tuple[Mapping[str, Any], ...]:
    """Apply the exact pinned erosion budget to every computed clearance.

    This is one deterministic budget calculation per interface, not a claim
    that physical material was cycled or that its real wear rate is known.
    ``wear_cycles`` in the release measurement names the pinned model horizon.
    """

    wear = binding["wear_model"]
    allowance = float(wear["cumulative_allowance_mm"])
    rows = []
    for clearance in clearances:
        observed = float(clearance["conservative_continuous_clearance_mm"])
        remaining = max(0.0, observed - allowance)
        required = float(clearance["required_clearance_mm"])
        rows.append(
            {
                "contract_index": clearance["contract_index"],
                "moving_part_id": clearance["moving_part_id"],
                "stationary_part_id": clearance["stationary_part_id"],
                "model_kind": wear["kind"],
                "model_version": wear["model_version"],
                "model_cycles": wear["cycles"],
                "model_basis": wear["basis"],
                "initial_conservative_clearance_mm": round(observed, 9),
                "pinned_cumulative_allowance_mm": allowance,
                "remaining_modeled_clearance_mm": round(remaining, 9),
                "required_clearance_mm": round(required, 9),
                "passed": remaining >= required,
            }
        )
    return tuple(rows)


def _failure_cases(
    contract: Mapping[str, Any],
    binding: Mapping[str, Any],
    clearances: Sequence[Mapping[str, Any]],
    wear_cases: Sequence[Mapping[str, Any]],
    loads: Sequence[Mapping[str, Any]],
    *,
    forward_passed: bool,
    reverse_passed: bool,
) -> Tuple[Mapping[str, Any], ...]:
    rows = []
    for bound in binding["failure_bindings"]:
        relevant_loads = [
            row for row in loads if row["contract_index"] in bound["load_case_indices"]
        ]
        mode_results = {}
        for mode in bound["verification_modes"]:
            if mode in _SUPPORTED_LOAD_MODES:
                selected = [row for row in relevant_loads if row["kind"] == mode]
                mode_results[mode] = bool(selected) and all(row["passed"] for row in selected)
            elif mode == "continuous-clearance":
                mode_results[mode] = (
                    bool(clearances)
                    and bool(wear_cases)
                    and all(row["passed"] for row in clearances)
                    and all(row["passed"] for row in wear_cases)
                )
            elif mode == "reverse-sweep":
                mode_results[mode] = reverse_passed
            elif mode == "stall-envelope":
                mode_results[mode] = bool(relevant_loads) and all(row["passed"] for row in relevant_loads)
        declared = contract["failure_modes"][bound["contract_index"]]
        rows.append(
            {
                "contract_index": bound["contract_index"],
                "mode": declared["mode"],
                "part_ids": list(bound["part_ids"]),
                "load_case_indices": list(bound["load_case_indices"]),
                "verification_modes": list(bound["verification_modes"]),
                "mode_results": mode_results,
                "forward_sweep_passed": forward_passed,
                "passed": bool(mode_results) and all(mode_results.values()),
            }
        )
    return tuple(rows)


def _receipt(
    *,
    artifact_sha256: str,
    capability: str,
    proof_class: str,
    role: str,
    source_sha256: Mapping[str, str],
    measurements: Mapping[str, Any],
    payload: Mapping[str, Any],
) -> Mapping[str, Any]:
    return {
        "schema_version": 1,
        "kind": "workshop.capability-release-receipt",
        "artifact_sha256": artifact_sha256,
        "capability": capability,
        "proof_class": proof_class,
        "role": role,
        "source_sha256": dict(source_sha256),
        "measurements": dict(measurements),
        "payload": dict(payload),
    }


def _write_receipts(
    evidence_root: Path,
    documents: Mapping[str, Mapping[str, Any]],
) -> Mapping[str, str]:
    root = Path(evidence_root)
    if not root.is_absolute() or root.is_symlink():
        raise ContractError("moving-machine evidence root must be an absolute regular directory")
    root.mkdir(parents=True, exist_ok=True)
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ContractError("moving-machine evidence root must be a directory")
    payloads = {path: _document_bytes(document) for path, document in documents.items()}
    targets = {path: root / path for path in documents}
    if any(path.exists() or path.is_symlink() for path in targets.values()):
        raise ContractError("moving-machine release receipts are immutable and already exist")
    digests = {}
    for relative, target in targets.items():
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            with target.open("xb") as handle:
                handle.write(payloads[relative])
        except FileExistsError as exc:
            raise ContractError("moving-machine release receipt already exists") from exc
        digests[relative] = hashlib.sha256(payloads[relative]).hexdigest()
    return digests


@dataclass(frozen=True)
class MovingMachineVerification:
    """Prepared deterministic checks that can be sealed after AI review.

    :meth:`WorkshopMovingMachineVerifier.run` never mutates the Playtest
    workspace.  A caller may therefore run all independent AI-player reviews
    first and call :meth:`seal` only after they pass.  A failed review leaves
    no partial release receipt behind.
    """

    mechanical_check: Mapping[str, Any]
    motion_check: Mapping[str, Any]
    mechanical_proof: Optional[CapabilityReleaseProof] = None
    motion_proof: Optional[CapabilityReleaseProof] = None
    receipt_sha256: Mapping[str, str] = field(default_factory=dict)
    _receipt_documents: Mapping[str, Mapping[str, Any]] = field(
        default_factory=dict, repr=False, compare=False
    )
    _proof_sources: Sequence[ReleaseProofSource] = field(
        default_factory=tuple, repr=False, compare=False
    )

    @property
    def passed(self) -> bool:
        return bool(self.mechanical_check.get("passed")) and bool(
            self.motion_check.get("passed")
        )

    @property
    def sealed(self) -> bool:
        return (
            self.mechanical_proof is not None
            and self.motion_proof is not None
            and bool(self.receipt_sha256)
        )

    def seal(self, evidence_root: Path) -> "MovingMachineVerification":
        """Write exact receipts and return a proof-bearing immutable result."""

        if not self.passed:
            raise ContractError("failed moving-machine checks cannot be sealed as release proof")
        if self.sealed:
            return self
        if not self._receipt_documents or not self._proof_sources:
            raise ContractError("moving-machine verification lacks prepared release documents")
        expected_documents = {
            WorkshopMovingMachineVerifier.MECHANICAL_RECEIPT_REF: (
                "mechanical-test",
                "computed-mechanical-proof",
                "mechanical-receipt",
                self.mechanical_check,
            ),
            WorkshopMovingMachineVerifier.MOTION_RECEIPT_REF: (
                "motion-test",
                "kinematic-motion-proof",
                "motion-receipt",
                self.motion_check,
            ),
        }
        expected_dependencies = {
            "product:%s" % source.path: source.sha256
            for source in self._proof_sources
        }
        if set(self._receipt_documents) != set(expected_documents):
            raise ContractError("prepared moving-machine receipt set changed before seal")
        for path, (capability, proof_class, role, check) in expected_documents.items():
            document = self._receipt_documents[path]
            if (
                document.get("artifact_sha256") != check.get("artifact_sha256")
                or document.get("capability") != capability
                or document.get("proof_class") != proof_class
                or document.get("role") != role
                or document.get("source_sha256") != expected_dependencies
                or document.get("measurements") != check.get("metrics")
            ):
                raise ContractError(
                    "prepared moving-machine receipt changed before seal"
                )
        receipt_hashes = _write_receipts(evidence_root, self._receipt_documents)
        mechanical_proof = CapabilityReleaseProof(
            capability="mechanical-test",
            artifact_sha256=self.mechanical_check["artifact_sha256"],
            proof_class="computed-mechanical-proof",
            sources=tuple(self._proof_sources)
            + (
                ReleaseProofSource(
                    "mechanical-receipt",
                    "playtest",
                    WorkshopMovingMachineVerifier.MECHANICAL_RECEIPT_REF,
                    receipt_hashes[
                        WorkshopMovingMachineVerifier.MECHANICAL_RECEIPT_REF
                    ],
                ),
            ),
            measurements=self.mechanical_check["metrics"],
        )
        motion_proof = CapabilityReleaseProof(
            capability="motion-test",
            artifact_sha256=self.motion_check["artifact_sha256"],
            proof_class="kinematic-motion-proof",
            sources=tuple(self._proof_sources)
            + (
                ReleaseProofSource(
                    "motion-receipt",
                    "playtest",
                    WorkshopMovingMachineVerifier.MOTION_RECEIPT_REF,
                    receipt_hashes[WorkshopMovingMachineVerifier.MOTION_RECEIPT_REF],
                ),
            ),
            measurements=self.motion_check["metrics"],
        )
        return MovingMachineVerification(
            self.mechanical_check,
            self.motion_check,
            mechanical_proof,
            motion_proof,
            receipt_hashes,
        )


class WorkshopMovingMachineVerifier:
    """Verify the shared one-axis rigid primitive moving-machine subset."""

    DESIGN_REF = "cad/design.json"
    DECLARATION_REF = "playtest/mechanical.json"
    BINDING_REF = "playtest/moving-machine-binding.json"
    PREFLIGHT_REF = "validation/cad-build.json"
    STEP_REF = "assembled.step"
    MECHANICAL_RECEIPT_REF = "receipts/moving-machine-mechanical.json"
    MOTION_RECEIPT_REF = "receipts/moving-machine-motion.json"

    def __init__(self, *, cad_builder: Optional[Any] = None) -> None:
        if cad_builder is None:
            cad_builder = locked_cad_project_verifier()
        if not callable(getattr(cad_builder, "check_motion", None)):
            raise ValueError("moving-machine verifier requires locked check_motion")
        self.cad_builder = cad_builder

    def run(
        self,
        *,
        artifact_sha256: str,
        product_root: Path,
        product_inventory: Mapping[str, str],
    ) -> MovingMachineVerification:
        _require_sha256(artifact_sha256, "moving-machine artifact sha256")
        root = Path(product_root)
        if not root.is_absolute() or root.is_symlink():
            raise ContractError("moving-machine product root must be an absolute regular directory")
        try:
            root = root.resolve(strict=True)
        except OSError as exc:
            raise ContractError("moving-machine product root is missing") from exc
        if not root.is_dir():
            raise ContractError("moving-machine product root must be a directory")
        if not isinstance(product_inventory, Mapping) or not product_inventory:
            raise ContractError("moving-machine product inventory is required")

        design, design_sha256 = _sealed_json(root, product_inventory, self.DESIGN_REF)
        declaration, declaration_sha256 = _sealed_json(
            root, product_inventory, self.DECLARATION_REF
        )
        binding_value, binding_sha256 = _sealed_json(root, product_inventory, self.BINDING_REF)
        preflight, preflight_sha256 = _sealed_json(root, product_inventory, self.PREFLIGHT_REF)
        unused_step_path, unused_step_bytes, step_sha256 = _safe_product_file(
            root, product_inventory, self.STEP_REF
        )
        del unused_step_path, unused_step_bytes

        action = design.get("action")
        if (
            design.get("kind") != "workshop-step-first-parametric-design"
            or not isinstance(action, Mapping)
        ):
            raise _wait(
                "mechanical-test",
                "The product lacks the shared sealed STEP-first CAD action.",
                "Regenerate Make with the common Workshop CAD provider before moving-machine Playtest.",
            )
        parts = moving_machine_parts(action)
        plan = declaration.get("digital_test_plan")
        contract = validate_moving_machine_lane_contract(
            plan.get("invent_lane_contract") if isinstance(plan, Mapping) else None
        )
        if (
            not isinstance(plan, Mapping)
            or plan.get("invent_lane_contract_sha256") != _json_sha256(contract)
        ):
            raise _wait(
                "mechanical-test",
                "Make's mechanical declaration is not bound to the exact Invent lane contract.",
                "Regenerate the common Workshop Make artifact from the sealed Invent result.",
            )
        binding = validate_moving_machine_binding(
            binding_value,
            design_sha256=design_sha256,
            action=action,
            contract=contract,
            parts=parts,
        )

        checks = preflight.get("checks")
        if not isinstance(checks, Mapping):
            raise _wait(
                "mechanical-test",
                "The sealed CAD preflight has no deterministic geometry checks.",
                "Rerun the shared locked CAD verifier on these exact Make bytes.",
            )
        brep = checks.get("brep")
        interference = checks.get("interference")
        interference_measurements = (
            interference.get("measurements") if isinstance(interference, Mapping) else None
        )
        if (
            not isinstance(brep, Mapping)
            or not isinstance(interference, Mapping)
            or not isinstance(interference_measurements, Mapping)
            or type(interference_measurements.get("poses_tested")) is not int
            or type(interference_measurements.get("forbidden_intersections")) is not int
        ):
            raise _wait(
                "mechanical-test",
                "The sealed CAD preflight lacks replayable B-rep/interference measurements.",
                "Rerun the shared locked CAD verifier before moving-machine Playtest.",
            )

        manifest = _motion_manifest(parts, binding)
        try:
            with tempfile.TemporaryDirectory(prefix="workshop-moving-machine-") as temporary:
                project = Path(temporary) / "cad"
                project.mkdir()
                _copy_locked_cad(root, product_inventory, action, project)
                motion_run = self.cad_builder.check_motion(
                    project, manifest, command_id="moving-machine-motion"
                )
        except WaitingFor:
            raise
        except (OSError, ContractError):
            raise
        except Exception as exc:
            raise _wait(
                "motion-test",
                "The locked Workshop motion checker could not evaluate the exact CAD assembly.",
                "Restore the shared CAD motion provider and resume these exact bytes.",
            ) from exc

        result = motion_run.get("result") if isinstance(motion_run, Mapping) else None
        rows = result.get("results") if isinstance(result, Mapping) else None
        expected_ids = [condition["id"] for condition in manifest["conditions"]]
        if (
            not isinstance(rows, list)
            or len(rows) != len(expected_ids)
            or [row.get("id") for row in rows if isinstance(row, Mapping)] != expected_ids
        ):
            raise _wait(
                "motion-test",
                "The locked Workshop motion checker returned incomplete or mismatched conditions.",
                "Rerun the exact generated manifest; an incomplete condition set is never a pass.",
            )
        if any(row.get("status") == "inconclusive" for row in rows):
            raise _wait(
                "motion-test",
                "At least one exact moving-machine condition was inconclusive.",
                "Repair the part labels or mechanism binding and rerun the shared CAD motion provider.",
            )

        by_id = {row["id"]: row for row in rows}
        assembly_passed = by_id["moving-machine-assembly-path"].get("status") == "pass"
        forward_passed = by_id["moving-machine-forward-sweep"].get("status") == "pass"
        reverse_passed = by_id["moving-machine-reverse-sweep"].get("status") == "pass"
        clearances = _clearance_cases(parts, action, contract, binding)
        wear_cases = _wear_cases(clearances, binding)
        loads = _load_cases(parts, contract, binding)
        failures = _failure_cases(
            contract,
            binding,
            clearances,
            wear_cases,
            loads,
            forward_passed=forward_passed,
            reverse_passed=reverse_passed,
        )
        fit_failures = sum(1 for row in clearances if not row["passed"])
        wear_failures = sum(1 for row in wear_cases if not row["passed"])
        load_failures = sum(1 for row in loads if not row["passed"])
        failure_failures = sum(1 for row in failures if not row["passed"])
        forbidden = interference_measurements["forbidden_intersections"]
        brep_valid = brep.get("status") == "passed"
        mechanical_measurements = {
            "brep_valid": brep_valid,
            "interference_cases": interference_measurements["poses_tested"],
            "fit_cases": len(clearances),
            "assembly_paths_tested": 1,
            "motion_cases": 2,
            "load_cases": len(loads),
            "failure_modes_tested": len(failures),
            "forbidden_intersections": forbidden,
            "fit_failures": fit_failures,
            "assembly_failures": 0 if assembly_passed else 1,
            "motion_failures": int(not forward_passed) + int(not reverse_passed),
            "load_failures": load_failures,
            "unresolved_critical_failures": failure_failures,
        }
        states_tested = sum(
            int(row.get("steps", binding["joint"]["steps"])) + 1
            for row in rows
            if row["id"] in {"moving-machine-forward-sweep", "moving-machine-reverse-sweep"}
        )
        motion_measurements = {
            "states_tested": states_tested,
            "continuous_sweep": True,
            "tolerance_cases_tested": len(clearances),
            "load_cases_tested": len(loads),
            # The locked B-rep and analytic clearance calculations above ran
            # in exactly the sealed assembly orientation. Global-orientation
            # invariance is not a substitute for gravity/load calculations.
            "orientations_tested": 1,
            "wear_cycles": _PINNED_WEAR_MODEL["cycles"],
            "misuse_cases_tested": len(binding["misuse_cases"]),
            "collisions": int(not forward_passed) + int(not reverse_passed),
            "stalls": load_failures,
            "failures": fit_failures + wear_failures + load_failures + failure_failures + int(not forward_passed) + int(not reverse_passed),
        }
        mechanical_passed = (
            brep_valid
            and all(type(value) is int and value >= 1 for key, value in mechanical_measurements.items() if key in {
                "interference_cases",
                "fit_cases",
                "assembly_paths_tested",
                "motion_cases",
                "load_cases",
                "failure_modes_tested",
            })
            and all(
                mechanical_measurements[name] == 0
                for name in (
                    "forbidden_intersections",
                    "fit_failures",
                    "assembly_failures",
                    "motion_failures",
                    "load_failures",
                    "unresolved_critical_failures",
                )
            )
        )
        motion_passed = (
            motion_measurements["states_tested"] >= 2
            and all(
                motion_measurements[name] >= 1
                for name in (
                    "tolerance_cases_tested",
                    "load_cases_tested",
                    "orientations_tested",
                    "wear_cycles",
                    "misuse_cases_tested",
                )
            )
            and all(
                motion_measurements[name] == 0
                for name in ("collisions", "stalls", "failures")
            )
        )
        source_refs = (
            self.STEP_REF,
            self.DESIGN_REF,
            self.DECLARATION_REF,
            self.BINDING_REF,
            self.PREFLIGHT_REF,
        )
        source_hashes = {
            self.STEP_REF: step_sha256,
            self.DESIGN_REF: design_sha256,
            self.DECLARATION_REF: declaration_sha256,
            self.BINDING_REF: binding_sha256,
            self.PREFLIGHT_REF: preflight_sha256,
        }
        config_sha256 = _json_sha256(
            {
                "binding_sha256": binding_sha256,
                "dimension_tolerance_mm": _DIMENSION_TOLERANCE_MM,
                "max_overlap_mm3": _MAX_OVERLAP_MM3,
                "pla_compression_mpa": _PLA_ALLOWABLE_COMPRESSION_MPA,
                "pla_shear_mpa": _PLA_ALLOWABLE_SHEAR_MPA,
                "wear_model": _PINNED_WEAR_MODEL,
                "checker_version": MOVING_MACHINE_CHECKER_VERSION,
            }
        )

        def check(capability: str, passed: bool, measurements: Mapping[str, Any]) -> Mapping[str, Any]:
            finding = []
            if not passed:
                finding.append(
                    {
                        "code": "%s-failed" % capability,
                        "area": capability,
                        "severity": "block",
                        "finding": "The exact rigid sweep, tolerance envelope, load screen, or bound failure case failed.",
                        "change": "Revise the mapped geometry, clearance, section, or mechanism contract and rerun the same shared verifier.",
                        "evidence_refs": list(source_refs),
                    }
                )
            return {
                "artifact_sha256": artifact_sha256,
                "capability": capability,
                "passed": passed,
                "checker": "workshop-primitive-moving-machine",
                "checker_version": MOVING_MACHINE_CHECKER_VERSION,
                "config_sha256": config_sha256,
                "method_class": (
                    "deterministic-mechanical-verification"
                    if capability == "mechanical-test"
                    else "deterministic-kinematic-simulation"
                ),
                "source_refs": list(source_refs),
                "observations": [
                    "Bound every typed Invent tolerance, load, and failure record to exact sealed primitive CAD part IDs.",
                    "Ran the locked exact-B-rep forward, reverse, and assembly sweeps plus a conservative all-angle swept-clearance envelope.",
                    "Applied bounded rigid-PLA compression/shear calculations to explicit loaded parts and support paths.",
                    "Applied the pinned versioned digital clearance-erosion budget to each interface; this is not a physical wear-rate test.",
                    "This digital result does not establish physical fit, retention, wear rate, durability, manufacture, or safety.",
                ],
                "metrics": dict(measurements),
                "findings": finding,
            }

        mechanical_check = check("mechanical-test", mechanical_passed, mechanical_measurements)
        motion_check = check("motion-test", motion_passed, motion_measurements)
        if not (mechanical_passed and motion_passed):
            return MovingMachineVerification(
                mechanical_check,
                motion_check,
            )

        proof_sources = (
            ReleaseProofSource("step-model", "product", self.STEP_REF, step_sha256),
            ReleaseProofSource("cad-design", "product", self.DESIGN_REF, design_sha256),
            ReleaseProofSource(
                "invent-contract", "product", self.DECLARATION_REF, declaration_sha256
            ),
            ReleaseProofSource(
                "machine-binding", "product", self.BINDING_REF, binding_sha256
            ),
            ReleaseProofSource(
                "cad-preflight", "product", self.PREFLIGHT_REF, preflight_sha256
            ),
        )
        dependency_hashes = {
            "product:%s" % source.path: source.sha256 for source in proof_sources
        }
        receipt_payload = {
            "claim_scope": "Deterministic rigid primitive CAD screening only; no physical or safety claim.",
            "binding": dict(binding),
            "motion_manifest": manifest,
            "motion_result": result,
            "clearance_cases": list(clearances),
            "wear_cases": list(wear_cases),
            "wear_measurement_scope": (
                "wear_cycles is the pinned digital model horizon. It does not "
                "count physically simulated or physically completed cycles."
            ),
            "load_cases": list(loads),
            "failure_cases": list(failures),
            "orientation_cases": [
                {
                    "orientation_id": "sealed-assembly-orientation",
                    "axis_convention": "+Z is the assembly and revolute axis",
                    "forward_sweep_passed": forward_passed,
                    "reverse_sweep_passed": reverse_passed,
                    "clearance_cases": len(clearances),
                    "load_cases": len(loads),
                    "passed": forward_passed
                    and reverse_passed
                    and all(row["passed"] for row in clearances)
                    and all(row["passed"] for row in loads),
                }
            ],
            "not_proven": list(_NOT_PROVEN),
        }
        receipt_documents = {
            self.MECHANICAL_RECEIPT_REF: _receipt(
                artifact_sha256=artifact_sha256,
                capability="mechanical-test",
                proof_class="computed-mechanical-proof",
                role="mechanical-receipt",
                source_sha256=dependency_hashes,
                measurements=mechanical_measurements,
                payload=receipt_payload,
            ),
            self.MOTION_RECEIPT_REF: _receipt(
                artifact_sha256=artifact_sha256,
                capability="motion-test",
                proof_class="kinematic-motion-proof",
                role="motion-receipt",
                source_sha256=dependency_hashes,
                measurements=motion_measurements,
                payload=receipt_payload,
            ),
        }
        return MovingMachineVerification(
            mechanical_check,
            motion_check,
            _receipt_documents=receipt_documents,
            _proof_sources=proof_sources,
        )


__all__ = [
    "MOVING_MACHINE_BINDING_KIND",
    "MOVING_MACHINE_BINDING_VERSION",
    "MovingMachineVerification",
    "WorkshopMovingMachineVerifier",
    "workshop_pinned_wear_model",
]
