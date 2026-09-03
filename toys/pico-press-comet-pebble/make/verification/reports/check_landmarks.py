"""Deterministic rest-energy sweep over the exact source tessellation."""

import importlib.util
import json
import math
from pathlib import Path

import numpy as np
from build123d import CenterOf

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "comet_pebble.step.py"
SPEC = importlib.util.spec_from_file_location("comet_pebble_entry", SOURCE)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
SHAPE = MODULE.gen_step()
VERTICES, _ = SHAPE.tessellate(0.02, 0.1)
POINTS = np.asarray([[point.X, point.Y, point.Z] for point in VERTICES])
center = SHAPE.center(CenterOf.MASS)
COM = np.asarray([center.X, center.Y, center.Z])

energies = []
for tilt_degrees in range(0, 181, 5):
    yaw_values = (0,) if tilt_degrees in (0, 180) else range(0, 360, 5)
    tilt = math.radians(tilt_degrees)
    for yaw_degrees in yaw_values:
        yaw = math.radians(yaw_degrees)
        up = np.asarray(
            [
                math.sin(tilt) * math.cos(yaw),
                math.sin(tilt) * math.sin(yaw),
                math.cos(tilt),
            ]
        )
        height = float(COM @ up - np.min(POINTS @ up))
        energies.append((height, tilt_degrees, yaw_degrees))

energies.sort()
global_minimum = energies[0]
alternate = min(row for row in energies if row[1] >= 10)
inverted = next(row for row in energies if row[1] == 180)
near_inverted = min(row for row in energies if row[1] == 175)
alternate_gap = alternate[0] - global_minimum[0]
inverted_gap = inverted[0] - global_minimum[0]
checks = {
    "upright_is_sampled_global_minimum": global_minimum[1] == 0,
    "alternate_10deg_or_more_is_over_1mm_higher": alternate_gap >= 1.0,
    "inverted_is_over_2mm_higher": inverted_gap >= 2.0,
    "inverted_is_not_a_sampled_local_minimum": near_inverted[0] < inverted[0],
}
result = {
    "schema_version": 1,
    "check": "comet-pebble-static-rest-energy",
    "ok": all(checks.values()),
    "checks": checks,
    "tessellation_tolerance_mm": 0.02,
    "angular_tolerance_rad": 0.1,
    "orientation_step_deg": 5,
    "sample_count": len(energies),
    "upright_com_height_mm": global_minimum[0],
    "best_alternate": {
        "com_height_mm": alternate[0],
        "tilt_deg": alternate[1],
        "yaw_deg": alternate[2],
        "gap_mm": alternate_gap,
    },
    "inverted_com_height_mm": inverted[0],
    "inverted_gap_mm": inverted_gap,
    "best_175deg_com_height_mm": near_inverted[0],
    "limitation": "Static uniform-density mesh sampling; not a trajectory, friction, impact, print, or physical settling test.",
}
print(json.dumps(result, sort_keys=True))
raise SystemExit(0 if result["ok"] else 2)
