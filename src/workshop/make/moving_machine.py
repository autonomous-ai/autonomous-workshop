"""Make-owned facts and bindings for the narrow moving-machine lane.

Make binds typed Invent assumptions to exact CAD part identifiers and seals
that declaration into the product.  Deterministic inspection and release
proof belong to :mod:`workshop.playtest.moving_machine`.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from typing import Any, Dict, Mapping, Sequence, Tuple

from workshop.errors import ContractError
from workshop.outcomes import Need, WaitingFor


MOVING_MACHINE_BINDING_KIND = "workshop.primitive-moving-machine-binding"
MOVING_MACHINE_BINDING_VERSION = 1
MOVING_MACHINE_CHECKER_VERSION = "1.0.0"

_SAFE_ID = re.compile(r"^[a-z][a-z0-9-]{0,62}$")
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


def _wait(capability: str, reason: str, instructions: str) -> WaitingFor:
    return WaitingFor(Need("playtest", capability, reason, instructions))


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _number(value: Any) -> bool:
    return type(value) in (int, float) and math.isfinite(float(value))


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


def moving_machine_parts(
    action: Mapping[str, Any],
) -> Mapping[str, Mapping[str, Any]]:
    """Validate and index the primitive parts named by a Make action."""

    return _part_by_id(action)


def validate_moving_machine_lane_contract(value: Any) -> Mapping[str, Any]:
    """Validate the typed Invent facts Make must bind to exact CAD parts."""

    return _validate_lane_contract(value)


def validate_moving_machine_binding(
    value: Any,
    *,
    design_sha256: str,
    action: Mapping[str, Any],
    contract: Mapping[str, Any],
    parts: Mapping[str, Mapping[str, Any]],
) -> Mapping[str, Any]:
    """Validate a sealed Make binding without performing Playtest behavior."""

    return _validate_binding(
        value,
        design_sha256=design_sha256,
        action=action,
        contract=contract,
        parts=parts,
    )


def __getattr__(name: str) -> Any:
    """Read the pre-0.6 verifier names from their Playtest owner lazily."""

    if name not in {"MovingMachineVerification", "WorkshopMovingMachineVerifier"}:
        raise AttributeError(name)
    from importlib import import_module

    value = getattr(import_module("workshop.playtest.moving_machine"), name)
    globals()[name] = value
    return value


__all__ = [
    "MOVING_MACHINE_BINDING_KIND",
    "MOVING_MACHINE_BINDING_VERSION",
    "moving_machine_parts",
    "validate_moving_machine_binding",
    "validate_moving_machine_lane_contract",
    "workshop_pinned_wear_model",
]
