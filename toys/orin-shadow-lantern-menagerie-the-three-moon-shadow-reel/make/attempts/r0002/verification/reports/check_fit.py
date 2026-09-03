#!/usr/bin/env python3
"""Project-specific, deterministic fit derivation audit."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
WORKSPACE = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(WORKSPACE / ".agents" / "skills" / "cad" / "scripts"))
sys.path.insert(0, str(PROJECT))

from lantern_menagerie_lib import (  # noqa: E402
    ASSEMBLY_DEPTH,
    BEARING_SOCKET_R,
    DETENT_FLAT_DEFLECTION,
    DETENT_HOME_DIFFERENTIAL,
    DETENT_NOSE_R,
    DETENT_OTHER_DEFLECTION,
    DETENT_POCKET_R,
    DETENT_RABBIT_DEFLECTION,
    HOOK_BARB_H,
    HOOK_BARB_W,
    HOOK_H,
    HOOK_LEAD_H,
    HOOK_LEAD_W,
    HOOK_SLOT_H,
    HOOK_SLOT_W,
    HOOK_W,
    REAR_INNER_Z,
    REEL_T,
    REEL_Z,
    SHELL_FACE_T,
    SPINDLE_BORE_D,
    SPINDLE_D,
    SPINDLE_LEN,
    STAND_HINGE_Z,
    TRUNNION_R,
)

checks = {
    "spindle_radial_clearance_mm": (SPINDLE_BORE_D - SPINDLE_D) / 2,
    "spindle_blind_end_clearance_mm": REAR_INNER_Z + 1.5 - (SHELL_FACE_T + SPINDLE_LEN),
    "reel_front_axial_gap_mm": REEL_Z - 2.4,
    "reel_rear_axial_gap_mm": REAR_INNER_Z - (REEL_Z + REEL_T),
    "hook_slot_x_clearance_mm": HOOK_SLOT_W - HOOK_W,
    "hook_slot_y_clearance_mm": HOOK_SLOT_H - HOOK_H,
    "hook_lead_x_clearance_mm": HOOK_SLOT_W - HOOK_LEAD_W,
    "hook_lead_y_clearance_mm": HOOK_SLOT_H - HOOK_LEAD_H,
    "hook_retention_x_each_side_mm": (HOOK_BARB_W - HOOK_SLOT_W) / 2,
    "hook_retention_y_each_side_mm": (HOOK_BARB_H - HOOK_SLOT_H) / 2,
    "detent_radial_clearance_mm": DETENT_POCKET_R - DETENT_NOSE_R,
    "detent_flat_deflection_mm": DETENT_FLAT_DEFLECTION,
    "detent_other_deflection_mm": DETENT_OTHER_DEFLECTION,
    "detent_rabbit_deflection_mm": DETENT_RABBIT_DEFLECTION,
    "detent_home_differential_mm": DETENT_HOME_DIFFERENTIAL,
    "stand_socket_radial_clearance_mm": BEARING_SOCKET_R - TRUNNION_R,
    "stand_hinge_behind_rear_outer_mm": STAND_HINGE_Z - ASSEMBLY_DEPTH,
}
limits = {
    "spindle_radial_clearance_mm": (0.29, 0.31),
    "spindle_blind_end_clearance_mm": (0.29, 0.31),
    "reel_front_axial_gap_mm": (0.29, 0.31),
    "reel_rear_axial_gap_mm": (0.29, 0.31),
    "hook_slot_x_clearance_mm": (0.30, 0.60),
    "hook_slot_y_clearance_mm": (0.30, 0.60),
    "hook_lead_x_clearance_mm": (0.19, 0.21),
    "hook_lead_y_clearance_mm": (0.19, 0.21),
    "hook_retention_x_each_side_mm": (0.29, 0.31),
    "hook_retention_y_each_side_mm": (0.29, 0.31),
    "detent_radial_clearance_mm": (0.19, 0.21),
    "detent_flat_deflection_mm": (0.49, 0.51),
    "detent_other_deflection_mm": (0.24, 0.26),
    "detent_rabbit_deflection_mm": (-0.01, 0.01),
    "detent_home_differential_mm": (0.24, 0.26),
    "stand_socket_radial_clearance_mm": (0.34, 0.36),
    "stand_hinge_behind_rear_outer_mm": (5.09, 5.11),
}
rows = []
for name, value in checks.items():
    low, high = limits[name]
    rows.append({
        "name": name,
        "observed_mm": round(value, 6),
        "expected_mm": [low, high],
        "passed": low <= value <= high,
    })
result = {
    "schema_version": 1,
    "kind": "lantern-menagerie.project-fit-audit",
    "method": "Paired clearances, detent travel, chamfered hook entry, and retained overhang are derived once from shared source constants; part builders do not restate a second nominal fit.",
    "ok": all(row["passed"] for row in rows),
    "checks": rows,
    "physical_limit": "Digital nominal clearances do not prove printer compensation, snap strain, detent feel, or cycle life.",
}
print(json.dumps(result, sort_keys=True, separators=(",", ":")))
raise SystemExit(0 if result["ok"] else 1)
