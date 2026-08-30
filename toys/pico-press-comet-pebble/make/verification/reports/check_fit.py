"""Uniform-density COM and landing-foot audit; not a physical motion test."""

import importlib.util
import json
import math
from pathlib import Path

from build123d import CenterOf
import numpy as np

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "comet_pebble.step.py"
SPEC = importlib.util.spec_from_file_location("comet_pebble_entry", SOURCE)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
SHAPE = MODULE.gen_step()
COM = SHAPE.center(CenterOf.MASS)
FOOT_RX = MODULE.BODY_STATIONS[0][1] - MODULE.SOLE_EDGE_FILLET
FOOT_RY = MODULE.BODY_STATIONS[0][2] - MODULE.SOLE_EDGE_FILLET
NORMALIZED = math.sqrt((COM.X / FOOT_RX) ** 2 + (COM.Y / FOOT_RY) ** 2)
RADIAL_MARGIN = (1.0 - NORMALIZED) * min(FOOT_RX, FOOT_RY)
INERTIA_XY = np.asarray(SHAPE.matrix_of_inertia, dtype=float)[:2, :2]
_, PRINCIPAL_VECTORS = np.linalg.eigh(INERTIA_XY)
PRINCIPAL_AXIS_DEG = math.degrees(
    math.atan2(PRINCIPAL_VECTORS[1, 0], PRINCIPAL_VECTORS[0, 0])
) % 180.0
LOWER_RAIL_AXIS_DEG = 10.0
AXIS_MISMATCH_DEG = abs(
    ((PRINCIPAL_AXIS_DEG - LOWER_RAIL_AXIS_DEG + 90.0) % 180.0) - 90.0
)
CAP = MODULE.BODY_STATIONS[-1]
CAP_ANGLE = math.radians(CAP[5])
CAP_DX = COM.X - CAP[3]
CAP_DY = COM.Y - CAP[4]
CAP_LOCAL_X = CAP_DX * math.cos(CAP_ANGLE) + CAP_DY * math.sin(CAP_ANGLE)
CAP_LOCAL_Y = -CAP_DX * math.sin(CAP_ANGLE) + CAP_DY * math.cos(CAP_ANGLE)
CAP_NORMALIZED_COM_RADIUS = math.sqrt(
    (CAP_LOCAL_X / CAP[1]) ** 2 + (CAP_LOCAL_Y / CAP[2]) ** 2
)
checks = {
    "com_projection_inside_foot": NORMALIZED < 1.0,
    "radial_margin_at_least_5mm": RADIAL_MARGIN >= 5.0,
    "com_below_half_height": COM.Z < SHAPE.bounding_box().size.Z / 2.0,
    "authored_section_sweep_at_least_20deg": (
        max(row[5] for row in MODULE.BODY_STATIONS)
        - min(row[5] for row in MODULE.BODY_STATIONS)
    ) >= 20.0,
    "measured_inertia_curvature_mismatch_10_to_20deg": (
        10.0 <= AXIS_MISMATCH_DEG <= 20.0
    ),
    "com_projection_outside_inverted_crown_cap": CAP_NORMALIZED_COM_RADIUS > 1.0,
}
result = {
    "schema_version": 1,
    "check": "comet-pebble-digital-balance",
    "ok": all(checks.values()),
    "checks": checks,
    "uniform_density_com_mm": [COM.X, COM.Y, COM.Z],
    "landing_ellipse_radii_mm": [FOOT_RX, FOOT_RY],
    "normalized_com_radius": NORMALIZED,
    "minimum_radial_margin_mm": RADIAL_MARGIN,
    "principal_inertia_axis_deg": PRINCIPAL_AXIS_DEG,
    "lower_rail_axis_deg": LOWER_RAIL_AXIS_DEG,
    "inertia_curvature_axis_mismatch_deg": AXIS_MISMATCH_DEG,
    "inverted_crown_cap_normalized_com_radius": CAP_NORMALIZED_COM_RADIUS,
    "limitation": "Geometry-only balance intent; no physical roll or settling test was run.",
}
print(json.dumps(result, sort_keys=True))
raise SystemExit(0 if result["ok"] else 2)
