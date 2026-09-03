"""Wish-specific deterministic geometry audit for Moonchase Fox."""

import json
import math
import os
import sys
from pathlib import Path

PROJECT = Path(os.environ.get("CAD_PROJECT_DIR", Path(__file__).resolve().parents[1]))
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

from moonchase_fox_lib import (  # noqa: E402
    DEPTH,
    MOON_CENTER,
    TRACK_CENTER_X,
    TRACK_CENTER_Y,
    TRACK_RADIUS,
    build_fox,
)


def main() -> int:
    shape = build_fox()
    bbox = shape.bounding_box()
    center = shape.center()
    rest_tilt_deg = math.degrees(
        math.atan2(abs(center.X - TRACK_CENTER_X), TRACK_CENTER_Y - center.Y)
    )
    checks = {
        "single_solid": len(shape.solids()) == 1,
        "flat_print_bed": abs(bbox.min.Z) <= 1e-6,
        "depth_mm": abs(bbox.size.Z - DEPTH) <= 0.05,
        "palm_envelope": bbox.size.X <= 110 and bbox.size.Y <= 91 and bbox.size.Z <= 30,
        "track_bottom_y": abs(bbox.min.Y) <= 0.05,
        "com_below_track_center": center.Y <= TRACK_CENTER_Y - 0.5,
        "com_horizontal_balance": abs(center.X - TRACK_CENTER_X) <= 0.1,
        "upright_equilibrium_deg": rest_tilt_deg <= 2.0,
        "track_contact_width_mm": DEPTH >= 20.0,
        "crescent_clearance_from_track": math.dist(MOON_CENTER, (TRACK_CENTER_X, 0.0)) > 20.0,
    }
    payload = {
        "schema_version": 1,
        "bbox_mm": [round(bbox.size.X, 4), round(bbox.size.Y, 4), round(bbox.size.Z, 4)],
        "center_of_mass_mm": [round(center.X, 4), round(center.Y, 4), round(center.Z, 4)],
        "track_center_mm": [TRACK_CENTER_X, TRACK_CENTER_Y],
        "predicted_rest_tilt_deg": round(rest_tilt_deg, 4),
        "checks": checks,
        "ok": all(checks.values()),
    }
    print(json.dumps(payload, sort_keys=True))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
