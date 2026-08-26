"""Public Make-stage contracts and CAD verification seams.

Heavy agent adapters remain available from their implementation modules;
other Workshop components should depend on the contracts exported here.
"""

from workshop.make.cad import (
    CadReleaseBundle,
    CadProjectVerifier,
    CadVerificationBuild,
    LOCKED_CAD_GENERATOR_ID,
    LOCKED_CAD_GENERATOR_VERSION,
    canonical_cad_project_sources,
    inspect_stl_topology,
    locked_cad_project_verifier,
    validate_cad_design_action,
)
from workshop.make.contracts import Feedback, Made, MakeContext
from workshop.make.moving_machine import (
    MOVING_MACHINE_BINDING_KIND,
    MOVING_MACHINE_BINDING_VERSION,
    moving_machine_parts,
    validate_moving_machine_binding,
    validate_moving_machine_lane_contract,
    workshop_pinned_wear_model,
)
from workshop.make.native import NATIVE_MADE_KIND, NativeMade
from workshop.make.ports import CadDoor, CadInspectionDoor, InspectionDoor, ModelDoor

__all__ = [
    "CadDoor",
    "CadInspectionDoor",
    "CadProjectVerifier",
    "CadReleaseBundle",
    "CadVerificationBuild",
    "Feedback",
    "InspectionDoor",
    "LOCKED_CAD_GENERATOR_ID",
    "LOCKED_CAD_GENERATOR_VERSION",
    "MOVING_MACHINE_BINDING_KIND",
    "MOVING_MACHINE_BINDING_VERSION",
    "NATIVE_MADE_KIND",
    "Made",
    "MakeContext",
    "ModelDoor",
    "NativeMade",
    "canonical_cad_project_sources",
    "inspect_stl_topology",
    "locked_cad_project_verifier",
    "validate_cad_design_action",
    "moving_machine_parts",
    "validate_moving_machine_binding",
    "validate_moving_machine_lane_contract",
    "workshop_pinned_wear_model",
]
