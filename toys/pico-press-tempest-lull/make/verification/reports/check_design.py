#!/usr/bin/env python3
"""Product-specific deterministic audit for Tempest Lull."""

import importlib.util
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tempest_lull.step.py"
spec = importlib.util.spec_from_file_location("tempest_lull", SOURCE)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)
shape = module.gen_step()
bb = shape.bounding_box()
com = shape.center(module.CenterOf.MASS)

checks = {
    "one_fused_solid": len(shape.solids()) == 1,
    "palm_sized_width_80_to_105_mm": 80 <= bb.size.X <= 105,
    "holdable_depth_at_least_18_mm": bb.size.Y >= 18,
    "bed_contact_z_zero": abs(bb.min.Z) <= 0.05,
    "stable_circular_keel_com_below_curvature_center": com.Z < module.KEEL_RADIUS,
    "left_right_balance": abs(com.X) <= 1.0,
    "rock_angle_crest_10_to_18_deg": 10 <= module.ROCK_ANGLE_DEG <= 18,
    "keel_min_radial_thickness_8_mm": (module.KEEL_RADIUS - module.KEEL_INNER_RADIUS) >= 8,
}

# Potential-energy rise about the circular keel center for the declared crest.
radius_to_com = module.KEEL_RADIUS - com.Z
crest_rise = radius_to_com * (1 - math.cos(math.radians(module.ROCK_ANGLE_DEG)))
report = {
    "schema_version": 1,
    "kind": "tempest-lull-design-check",
    "ok": all(checks.values()),
    "checks": checks,
    "measurements_mm": {
        "bbox_x": round(bb.size.X, 3),
        "bbox_y": round(bb.size.Y, 3),
        "bbox_z": round(bb.size.Z, 3),
        "center_of_mass_x": round(com.X, 3),
        "center_of_mass_z": round(com.Z, 3),
        "curvature_center_z": module.KEEL_RADIUS,
        "estimated_crest_com_rise": round(crest_rise, 3),
    },
    "limits": "Rigid-body geometry only; no claim of a successful physical print or measured rocking duration.",
}
print(json.dumps(report, indent=2, sort_keys=True))
raise SystemExit(0 if report["ok"] else 1)
