#!/usr/bin/env python3
"""Independent connector-ledger audit without duplicating geometry checks."""

import json
import math
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))
from params import *  # noqa: E402,F403

checks = {
    "trunnion_diameter_mm": TRUNNION_D,
    "seat_diameter_mm": SEAT_D,
    "trunnion_radial_clearance_mm": (SEAT_D - TRUNNION_D) / 2.0,
    "axial_clearance_each_mm": AXIAL_CLEARANCE_EACH,
    "seam_key_clearance_each_mm": KEY_CLEARANCE,
    "magazine_clearance_each_mm": MAG_CLEARANCE,
    "lap_width_mm": LAP_W,
    "bridge_slide_mm": BRIDGE_SLIDE,
    "foot_vertical_clearance_mm": FOOT_VERTICAL_CLEARANCE,
    "retaining_shoulder_thickness_mm": RETAINING_SHOULDER_T,
}
assert math.isclose(checks["trunnion_radial_clearance_mm"], 0.30, abs_tol=1e-9)
assert 0.30 <= checks["axial_clearance_each_mm"] <= 0.40
assert checks["seam_key_clearance_each_mm"] == 0.30
assert checks["magazine_clearance_each_mm"] == 0.30
assert checks["lap_width_mm"] == 2.0
assert checks["bridge_slide_mm"] == 6.0
assert checks["foot_vertical_clearance_mm"] == 0.25
assert checks["retaining_shoulder_thickness_mm"] == 2.5
assert {"tray_a", "tray_b", "gate_bridge", "gravity_blade", "gate_keeper",
        "seam_storage_key", "ready_spent_magazine"}
print(json.dumps({"ok": True, "connector_ledger": checks}, sort_keys=True))
