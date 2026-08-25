"""Workshop-owned deterministic verification for a narrow moving-machine lane.

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

from .errors import ContractError
from .jobs import Need, WaitingFor
from .playtest_release import CapabilityReleaseProof, ReleaseProofSource


MOVING_MACHINE_BINDING_KIND = "workshop.primitive-moving-machine-binding"
MOVING_MACHINE_BINDING_VERSION = 1
MOVING_MACHINE_CHECKER_VERSION = "1.0.0"

_DIMENSION_TOLERANCE_MM = 0.2
_MAX_OVERLAP_MM3 = 0.001
_PLA_ALLOWABLE_COMPRESSION_MPA = 5.0
_PLA_ALLOWABLE_SHEAR_MPA = 3.0
_EXECUTABLE_SUFFIXES = frozenset(
    (".py", ".pyc", ".pyo", ".so", ".dylib", ".pyd", ".pth")
)
_SAFE_ID = re.compile(r"^[a-z][a-z0-9-]{0,62}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_SUPPORTED_LOAD_MODES = frozenset(("bulk-compression", "direct-shear"))
_SUPPORTED_FAILURE_MODES = frozenset(
    (
        "bulk-compression",
        "direct-shear",
        "continuous-clearance",
        "reverse-sweep",
        "stall-envelope",
    )
)
_PINNED_WEAR_MODEL = {
    "kind": "workshop-pinned-digital-clearance-budget",
    "model_version": "1.0.0",
    "cycles": 1_000,
    "cumulative_allowance_mm": 0.2,
    "basis": (
        "The 1,000-cycle value is a pinned digital model horizon used with a "
        "fixed 0.2 mm cumulative clearance erosion budget. No physical cycles "
        "are simulated or claimed."
    ),
}


def workshop_pinned_wear_model() -> Mapping[str, Any]:
    """Return the Workshop-owned digital wear budget sealed by Make.

    This is configuration for a conservative clearance calculation, not a
    model-authored choice and not evidence that physical cycles occurred.
    """

    return dict(_PINNED_WEAR_MODEL)
_SAFETY_HAZARD = re.compile(
    r"\b(?:pinch(?:ing|ed)?|entrap(?:ment)?|injur(?:y|ies)|chok(?:e|ing)|ingest(?:ion|ed)?|"
    r"suffocat(?:e|ion)|strangulat(?:e|ion)|lacerat(?:e|ion)|cut(?:ting)?|"
    r"burn(?:ing)?|electric(?:al)?\s+shock|toxic(?:ity)?|poison(?:ing)?|"
    r"sharp\s+edge|eye\s+hazard|small\s+parts?|safety[- ]critical|unsafe|hazard)\b",
    re.IGNORECASE,
)
_UNSUPPORTED_FAILURE_PHYSICS = re.compile(
    r"\b(?:fatigue|abras(?:ion|ive)|material\s+wear|spring|gear(?:ing)?|"
    r"gear[- ]?tooth|bending|buckl(?:e|ing)|torsion|impact|creep|"
    r"snap[- ]?fit|living\s+hinge|friction|retention)\b",
    re.IGNORECASE,
)
_SUPPORTED_FAILURE_SEMANTICS = re.compile(
    r"\b(?:shear|compress(?:ion|ed)?|clearance|stall|jam(?:ming|med)?|"
    r"interfer(?:ence|es)|collid(?:e|es|ed)|collision)\b",
    re.IGNORECASE,
)
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


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _number(value: Any) -> bool:
    return type(value) in (int, float) and math.isfinite(float(value))


def _require_sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise ContractError("%s must be a lowercase SHA-256" % label)
    return value


def _exact_keys(value: Any, keys: Sequence[str], label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != set(keys):
        raise _wait(
            "motion-test",
            "%s is missing or uses an unsupported schema." % label,
            "Regenerate the sealed moving-machine binding with the shared Workshop Make provider.",
        )
    return value


def _indices(records: Any, expected_count: int, label: str) -> Tuple[Mapping[str, Any], ...]:
    if (
        not isinstance(records, list)
        or len(records) != expected_count
        or not all(isinstance(item, Mapping) for item in records)
    ):
        raise _wait(
            "mechanical-test",
            "%s does not bind every Invent record exactly once." % label,
            "Have shared Make map every typed Invent record to exact CAD part IDs; do not infer missing mappings during Playtest.",
        )
    observed = [item.get("contract_index") for item in records]
    if (
        not all(type(index) is int for index in observed)
        or sorted(observed) != list(range(expected_count))
        or len(observed) != len(set(observed))
    ):
        raise _wait(
            "mechanical-test",
            "%s contains missing, duplicate, or out-of-range Invent indexes." % label,
            "Regenerate the exact Workshop moving-machine binding before Playtest.",
        )
    return tuple(records)


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


def _part_by_id(action: Mapping[str, Any]) -> Mapping[str, Mapping[str, Any]]:
    parts = action.get("parts")
    if not isinstance(parts, list):
        raise _wait(
            "mechanical-test",
            "The sealed CAD action has no primitive part inventory.",
            "Regenerate the design with the shared STEP-first box/cylinder Make provider.",
        )
    indexed: Dict[str, Mapping[str, Any]] = {}
    for part in parts:
        if not isinstance(part, Mapping):
            raise _wait(
                "mechanical-test",
                "The sealed CAD action contains a malformed primitive part.",
                "Regenerate the design with the shared STEP-first Make provider.",
            )
        identifier = part.get("part_id")
        size = part.get("size_mm")
        center = part.get("assembly_center_mm")
        if (
            not isinstance(identifier, str)
            or _SAFE_ID.fullmatch(identifier) is None
            or identifier in indexed
            or part.get("shape") not in {"box", "cylinder"}
            or str(part.get("material", "")).casefold() != "pla"
            or not isinstance(size, Mapping)
            or set(size) != {"x", "y", "z"}
            or not all(_number(size.get(axis)) and float(size[axis]) > 0 for axis in ("x", "y", "z"))
            or not isinstance(center, Mapping)
            or set(center) != {"x", "y", "z"}
            or not all(_number(center.get(axis)) for axis in ("x", "y", "z"))
            or not _number(part.get("assembly_rotation_deg"))
        ):
            raise _wait(
                "mechanical-test",
                "The moving machine uses geometry or material outside the shared rigid PLA primitive verifier.",
                "Use rigid PLA box/cylinder parts with finite dimensions and assembly poses, or connect a Workshop verifier for the actual geometry/material.",
            )
        indexed[identifier] = part
    if len(indexed) < 2:
        raise _wait(
            "mechanical-test",
            "A moving machine needs at least two exact CAD parts for motion and support.",
            "Regenerate Make with a moving part and at least one distinct support or obstacle part.",
        )
    return indexed


def _validate_lane_contract(value: Any) -> Mapping[str, Any]:
    contract = _exact_keys(
        value,
        (
            "schema_version",
            "lane",
            "kinematic_model",
            "tolerances_mm",
            "load_assumptions",
            "failure_modes",
        ),
        "Invent moving-machine contract",
    )
    kinematics = contract.get("kinematic_model")
    if (
        contract.get("schema_version") != 1
        or contract.get("lane") != "moving-machines"
        or not isinstance(kinematics, Mapping)
        or set(kinematics)
        != {"input_motion", "transmission", "output_motion", "degrees_of_freedom"}
        or not _text(kinematics.get("input_motion"))
        or not isinstance(kinematics.get("transmission"), list)
        or not kinematics["transmission"]
        or not all(_text(item) for item in kinematics["transmission"])
        or not _text(kinematics.get("output_motion"))
    ):
        raise _wait(
            "motion-test",
            "The sealed Invent kinematic contract is incomplete.",
            "Resume shared Invent until it emits the exact typed moving-machine lane contract.",
        )
    if kinematics.get("degrees_of_freedom") != 1:
        raise _wait(
            "motion-test",
            "The shared primitive motion verifier currently supports exactly one degree of freedom.",
            "Connect the Workshop multi-link dynamics provider for this sealed mechanism; the Inventor does not need to supply one.",
        )
    tolerances = contract.get("tolerances_mm")
    loads = contract.get("load_assumptions")
    failures = contract.get("failure_modes")
    if not isinstance(tolerances, list) or not tolerances:
        raise _wait(
            "motion-test",
            "Invent supplied no numeric moving-interface tolerance envelope.",
            "Resume shared Invent with nominal clearance and tolerance records before Make.",
        )
    for record in tolerances:
        if (
            not isinstance(record, Mapping)
            or set(record) != {"interface", "nominal_clearance_mm", "tolerance_mm"}
            or not _text(record.get("interface"))
            or not _number(record.get("nominal_clearance_mm"))
            or float(record["nominal_clearance_mm"]) < 0
            or not _number(record.get("tolerance_mm"))
            or float(record["tolerance_mm"]) < 0
        ):
            raise _wait(
                "motion-test",
                "Invent supplied an invalid moving-interface tolerance record.",
                "Resume shared Invent with finite non-negative nominal clearance and tolerance values.",
            )
    if not isinstance(loads, list) or not loads:
        raise _wait(
            "mechanical-test",
            "Invent supplied no bounded load assumptions for the moving machine.",
            "Resume shared Invent with force, safety factor, and basis for every critical load case.",
        )
    for record in loads:
        if (
            not isinstance(record, Mapping)
            or set(record) != {"case", "force_n", "safety_factor", "basis"}
            or not _text(record.get("case"))
            or not _number(record.get("force_n"))
            or float(record["force_n"]) < 0
            or not _number(record.get("safety_factor"))
            or float(record["safety_factor"]) < 1
            or not _text(record.get("basis"))
        ):
            raise _wait(
                "mechanical-test",
                "Invent supplied an invalid moving-machine load assumption.",
                "Resume shared Invent with finite force and safety-factor records.",
            )
    if not isinstance(failures, list) or not failures:
        raise _wait(
            "mechanical-test",
            "Invent supplied no explicit moving-machine failure modes.",
            "Resume shared Invent with cause, effect, and mitigation for each critical failure.",
        )
    for record in failures:
        if (
            not isinstance(record, Mapping)
            or set(record) != {"mode", "cause", "effect", "mitigation"}
            or not all(_text(record.get(key)) for key in ("mode", "cause", "effect", "mitigation"))
        ):
            raise _wait(
                "mechanical-test",
                "Invent supplied an invalid moving-machine failure-mode record.",
                "Resume shared Invent with bounded cause, effect, and mitigation text.",
            )
    return contract


def _validate_binding(
    value: Any,
    *,
    design_sha256: str,
    action: Mapping[str, Any],
    contract: Mapping[str, Any],
    parts: Mapping[str, Mapping[str, Any]],
) -> Mapping[str, Any]:
    binding = _exact_keys(
        value,
        (
            "schema_version",
            "kind",
            "cad_design_sha256",
            "invent_lane_contract_sha256",
            "joint",
            "tolerance_bindings",
            "load_bindings",
            "failure_bindings",
            "wear_model",
            "misuse_cases",
        ),
        "sealed moving-machine binding",
    )
    if (
        binding.get("schema_version") != MOVING_MACHINE_BINDING_VERSION
        or binding.get("kind") != MOVING_MACHINE_BINDING_KIND
        or binding.get("cad_design_sha256") != design_sha256
        or binding.get("invent_lane_contract_sha256") != _json_sha256(contract)
    ):
        raise _wait(
            "motion-test",
            "The moving-machine binding is not bound to the exact CAD design and Invent contract.",
            "Have shared Make regenerate the binding from these sealed bytes; never reuse one from another revision.",
        )

    motion = action.get("motion_spec")
    if (
        not isinstance(motion, Mapping)
        or motion.get("enabled") is not True
        or motion.get("axis") != "z"
        or motion.get("moving_part_id") not in parts
        or type(motion.get("sweep_degrees")) is not int
        or not 1 <= motion["sweep_degrees"] <= 360
        or not _number(motion.get("minimum_aabb_clearance_mm"))
        or float(motion["minimum_aabb_clearance_mm"]) < 0
    ):
        raise _wait(
            "motion-test",
            "The exact Make action is not a supported bounded Z-axis moving primitive.",
            "Regenerate shared Make with one enabled rigid Z-axis motion, or connect the Workshop provider for the actual joint type.",
        )
    joint = _exact_keys(
        binding.get("joint"),
        (
            "joint_id",
            "kind",
            "moving_part_id",
            "support_part_ids",
            "obstacle_part_ids",
            "axis_point_mm",
            "axis_direction",
            "start_deg",
            "end_deg",
            "steps",
        ),
        "moving-machine joint binding",
    )
    moving_id = motion["moving_part_id"]
    stationary = set(parts) - {moving_id}
    supports = joint.get("support_part_ids")
    obstacles = joint.get("obstacle_part_ids")
    axis_point = joint.get("axis_point_mm")
    expected_center = parts[moving_id]["assembly_center_mm"]
    minimum_steps = max(36, int(math.ceil(float(motion["sweep_degrees"]) / 5.0)))
    if (
        not _text(joint.get("joint_id"))
        or _SAFE_ID.fullmatch(str(joint["joint_id"])) is None
        or joint.get("kind") != "rigid-revolute-z"
        or joint.get("moving_part_id") != moving_id
        or not isinstance(supports, list)
        or not supports
        or not isinstance(obstacles, list)
        or not obstacles
        or not all(isinstance(item, str) for item in supports + obstacles)
        or len(supports) != len(set(supports))
        or len(obstacles) != len(set(obstacles))
        or set(supports) & set(obstacles)
        or set(supports) | set(obstacles) != stationary
        or not isinstance(axis_point, list)
        or len(axis_point) != 3
        or not all(_number(item) for item in axis_point)
        or any(
            not math.isclose(float(axis_point[index]), float(expected_center[axis]), abs_tol=1e-9)
            for index, axis in enumerate(("x", "y", "z"))
        )
        or joint.get("axis_direction") != [0.0, 0.0, 1.0]
        or not _number(joint.get("start_deg"))
        or float(joint["start_deg"]) != 0.0
        or not _number(joint.get("end_deg"))
        or float(joint["end_deg"]) != float(motion["sweep_degrees"])
        or type(joint.get("steps")) is not int
        or not minimum_steps <= joint["steps"] <= 720
    ):
        raise _wait(
            "motion-test",
            "The sealed joint binding is not the shared one-axis rigid primitive contract.",
            "Have shared Make name exact support/obstacle parts and a centered assembly-Z revolute axis, or connect the Workshop provider for the actual mechanism.",
        )

    tolerance_bindings = _indices(
        binding.get("tolerance_bindings"), len(contract["tolerances_mm"]), "tolerance bindings"
    )
    for record in tolerance_bindings:
        if (
            set(record)
            != {"contract_index", "moving_part_id", "stationary_part_ids", "verification"}
            or record.get("moving_part_id") != moving_id
            or record.get("verification") != "continuous-swept-envelope"
            or not isinstance(record.get("stationary_part_ids"), list)
            or not record["stationary_part_ids"]
            or len(record["stationary_part_ids"])
            != len(set(record["stationary_part_ids"]))
            or not set(record["stationary_part_ids"]) <= set(obstacles)
        ):
            raise _wait(
                "motion-test",
                "A tolerance is not mapped to exact moving and stationary primitive part IDs.",
                "Have shared Make bind each Invent tolerance to the exact obstacle interface covered by the continuous swept envelope.",
            )
    if {
        part_id
        for record in tolerance_bindings
        for part_id in record["stationary_part_ids"]
    } != set(obstacles):
        raise _wait(
            "motion-test",
            "The tolerance bindings do not cover every obstacle in the declared rotary sweep.",
            "Have shared Make map every exact obstacle part into at least one Invent tolerance envelope.",
        )

    load_bindings = _indices(
        binding.get("load_bindings"), len(contract["load_assumptions"]), "load bindings"
    )
    for record in load_bindings:
        modes = record.get("verification_modes")
        if (
            set(record)
            != {
                "contract_index",
                "loaded_part_id",
                "support_part_ids",
                "section_axis",
                "verification_modes",
            }
            or record.get("loaded_part_id") not in parts
            or not isinstance(record.get("support_part_ids"), list)
            or not record["support_part_ids"]
            or not all(isinstance(item, str) for item in record["support_part_ids"])
            or len(record["support_part_ids"])
            != len(set(record["support_part_ids"]))
            or not set(record["support_part_ids"])
            <= set(parts) - {record["loaded_part_id"]}
            or record.get("section_axis") != "z"
            or not isinstance(modes, list)
            or not modes
            or len(modes) != len(set(modes))
            or not set(modes) <= _SUPPORTED_LOAD_MODES
        ):
            raise _wait(
                "mechanical-test",
                "A load assumption is not mapped to a supported exact primitive load path.",
                "Have shared Make bind every Invent force case to a loaded part, support parts, and the supported compression/shear section checks, or connect a richer Workshop solver.",
            )

    failure_bindings = _indices(
        binding.get("failure_bindings"), len(contract["failure_modes"]), "failure bindings"
    )
    for record in failure_bindings:
        part_ids = record.get("part_ids")
        load_indexes = record.get("load_case_indices")
        modes = record.get("verification_modes")
        if (
            set(record)
            != {"contract_index", "part_ids", "load_case_indices", "verification_modes"}
            or not isinstance(part_ids, list)
            or not part_ids
            or not all(isinstance(item, str) for item in part_ids)
            or len(part_ids) != len(set(part_ids))
            or not set(part_ids) <= set(parts)
            or not isinstance(load_indexes, list)
            or not load_indexes
            or len(load_indexes) != len(set(load_indexes))
            or not all(type(index) is int and 0 <= index < len(load_bindings) for index in load_indexes)
            or not isinstance(modes, list)
            or not modes
            or len(modes) != len(set(modes))
            or not set(modes) <= _SUPPORTED_FAILURE_MODES
        ):
            raise _wait(
                "mechanical-test",
                "A declared failure mode lacks a complete deterministic CAD/load binding.",
                "Have shared Make map every failure to exact parts, Invent load indexes, and supported verification modes; otherwise connect the appropriate Workshop solver.",
            )
        for mode in set(modes) & _SUPPORTED_LOAD_MODES:
            if not any(
                mode in load_bindings[index]["verification_modes"]
                for index in load_indexes
            ):
                raise _wait(
                    "mechanical-test",
                    "A failure-mode load check is not present in its cited load bindings.",
                    "Regenerate the shared binding so every claimed verification mode has an actual deterministic calculation.",
                )
        if "continuous-clearance" in modes and not tolerance_bindings:
            raise _wait(
                "motion-test",
                "A clearance failure mode has no numeric tolerance case.",
                "Return to shared Invent/Make and bind it to an exact clearance envelope.",
            )

        declared_failure = contract["failure_modes"][record["contract_index"]]
        failure_text = " ".join(
            str(declared_failure[key])
            for key in ("mode", "cause", "effect", "mitigation")
        )
        hazard = _SAFETY_HAZARD.search(failure_text)
        if hazard is not None:
            raise _wait(
                "mechanical-safety-test",
                "The declared failure mode includes a %s hazard, which generic clearance/load math cannot verify."
                % hazard.group(0).casefold(),
                "Connect the shared Workshop hazard and pinch-point provider, followed by the required physical safety evaluation; do not relabel this as a generic load or clearance pass.",
            )
        unsupported = _UNSUPPORTED_FAILURE_PHYSICS.search(failure_text)
        if unsupported is not None:
            raise _wait(
                "mechanical-test",
                "The declared failure mode needs %s physics outside the rigid primitive solver."
                % unsupported.group(0).casefold(),
                "Connect the shared Workshop solver for this exact failure physics; do not count a generic clearance or section calculation as verification.",
            )
        if _SUPPORTED_FAILURE_SEMANTICS.search(failure_text) is None:
            raise _wait(
                "mechanical-test",
                "The declared failure semantics are not covered by the shared clearance/compression/shear solver.",
                "Map the failure to a Workshop provider that computes its actual physics instead of relabelling it as a generic primitive check.",
            )

    wear = _exact_keys(
        binding.get("wear_model"),
        ("kind", "model_version", "cycles", "cumulative_allowance_mm", "basis"),
        "moving-machine wear envelope",
    )
    if dict(wear) != _PINNED_WEAR_MODEL:
        raise _wait(
            "motion-test",
            "The mechanism does not use the pinned Workshop digital wear-clearance budget.",
            "Regenerate the shared Make binding with the exact versioned Workshop wear envelope, or connect a source-bound material wear provider. An arbitrary cycle count cannot pass.",
        )
    misuse = binding.get("misuse_cases")
    if (
        not isinstance(misuse, list)
        or len(misuse) != len(set(misuse))
        or set(misuse) != {"reverse-sweep", "stall-load-envelope"}
    ):
        raise _wait(
            "motion-test",
            "The shared moving-machine binding lacks reverse-motion and stall-load misuse cases.",
            "Regenerate the binding with both deterministic misuse screens.",
        )
    return binding


def _z_bounds(part: Mapping[str, Any]) -> Tuple[float, float]:
    center = part["assembly_center_mm"]
    base = float(center["z"])
    return base, base + float(part["size_mm"]["z"])


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
    from .agent_make import LockedCadSkillBuilder

    expected_sources = LockedCadSkillBuilder._project_sources(action)
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
            from .agent_make import LockedCadSkillBuilder

            cad_builder = LockedCadSkillBuilder()
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
        parts = _part_by_id(action)
        plan = declaration.get("digital_test_plan")
        contract = _validate_lane_contract(
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
        binding = _validate_binding(
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
