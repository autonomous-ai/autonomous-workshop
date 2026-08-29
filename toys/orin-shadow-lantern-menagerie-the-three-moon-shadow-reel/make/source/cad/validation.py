"""Algebraic parameter audit; geometry gates remain external."""

import math

from params import *


def parameter_audit() -> dict[str, float | int]:
    return {
        "part_count": 4,
        "reel_diameter_mm": REEL_D,
        "portal_diameter_mm": PORTAL_D,
        "portal_offset_mm": PORTAL_Y,
        "spindle_diameter_mm": SPINDLE_D,
        "spindle_bore_diameter_mm": SPINDLE_BORE_D,
        "spindle_radial_clearance_mm": (SPINDLE_BORE_D - SPINDLE_D) / 2,
        "axial_gap_each_side_mm": AXIAL_GAP,
        "rear_face_thickness_mm": REAR_FACE_T,
        "hook_lead_x_clearance_mm": HOOK_SLOT_W - HOOK_LEAD_W,
        "hook_lead_y_clearance_mm": HOOK_SLOT_H - HOOK_LEAD_H,
        "hook_required_one_axis_flex_mm": HOOK_REQUIRED_FLEX,
        "hook_positive_retention_overhang_mm": HOOK_REQUIRED_FLEX,
        "detent_radial_clearance_mm": DETENT_POCKET_R - DETENT_NOSE_R,
        "detent_flat_deflection_mm": DETENT_FLAT_DEFLECTION,
        "detent_other_deflection_mm": DETENT_OTHER_DEFLECTION,
        "detent_rabbit_deflection_mm": DETENT_RABBIT_DEFLECTION,
        "detent_home_differential_mm": DETENT_HOME_DIFFERENTIAL,
        "detent_nose_tip_radius_mm": DETENT_NOSE_R - DETENT_NOSE_CHAMFER,
        "detent_pocket_ramp_radial_run_mm": DETENT_POCKET_MOUTH_R - DETENT_POCKET_R,
        "detent_pocket_ramp_depth_mm": DETENT_POCKET_RAMP_DEPTH,
        "min_web_mm": MIN_WEB,
        "stand_deploy_rotation_deg": STAND_DEPLOY_DEG,
        "frame_height_mm": FRAME_TOP_Y - FRAME_BOTTOM_Y,
    }


assert math.isclose(SPINDLE_D, 7.2, abs_tol=1e-9)
assert math.isclose(REAR_INNER_Z - (REEL_Z + REEL_T), AXIAL_GAP, abs_tol=1e-9)
assert math.isclose(HOOK_SLOT_W - HOOK_LEAD_W, 0.4, abs_tol=1e-9)
assert math.isclose(HOOK_SLOT_H - HOOK_LEAD_H, 0.4, abs_tol=1e-9)
assert math.isclose(HOOK_REQUIRED_FLEX, 0.6, abs_tol=1e-9)
assert math.isclose(DETENT_HOME_DIFFERENTIAL, 0.25, abs_tol=1e-9)
assert DETENT_POCKET_MOUTH_R > DETENT_POCKET_R
assert DETENT_POCKET_RAMP_DEPTH < DETENT_POCKET_DEPTH_OTHER
assert math.isclose(STAND_DEPLOY_DEG, 112.0, abs_tol=1e-9)
assert FRAME_TOP_Y - FRAME_BOTTOM_Y <= 130.0
assert REEL_D <= 114.0
