#!/usr/bin/env python3
"""Deterministic local audit of sealed dimensions and printable part bodies."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
WORKSPACE = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(WORKSPACE / ".agents" / "skills" / "cad" / "scripts"))
sys.path.insert(0, str(PROJECT))

from lantern_menagerie_lib import (  # noqa: E402
    AXIAL_GAP,
    FRAME_BOTTOM_Y,
    FRAME_TOP_Y,
    PORTAL_D,
    PORTAL_Y,
    REEL_D,
    REEL_T,
    SPINDLE_BORE_D,
    SPINDLE_D,
    STAND_DEPLOY_DEG,
    make_assembly,
    make_front_shell,
    make_kickstand,
    make_rear_shell,
    make_shadow_reel,
    parameter_audit,
)


def close(a: float, b: float, tol: float = 0.10) -> bool:
    return math.isclose(a, b, abs_tol=tol)


parts = {
    "front_shell": make_front_shell(),
    "rear_shell": make_rear_shell(),
    "shadow_reel": make_shadow_reel(),
    "kickstand": make_kickstand(),
}
assembly = make_assembly()
checks: list[dict[str, object]] = []


def record(name: str, passed: bool, observed: object, expected: object) -> None:
    checks.append({"name": name, "passed": bool(passed), "observed": observed, "expected": expected})


for name, shape in parts.items():
    box = shape.bounding_box()
    record(f"{name}.single_solid", len(shape.solids()) == 1, len(shape.solids()), 1)
    record(f"{name}.positive_volume", shape.volume > 0, round(shape.volume, 3), "> 0")
    record(f"{name}.bed_z", close(box.min.Z, 0.0), round(box.min.Z, 4), 0.0)

reel_box = parts["shadow_reel"].bounding_box()
record("reel.diameter_x", close(reel_box.size.X, REEL_D), round(reel_box.size.X, 3), REEL_D)
record("reel.diameter_y", close(reel_box.size.Y, REEL_D), round(reel_box.size.Y, 3), REEL_D)
record("reel.thickness", close(reel_box.size.Z, REEL_T), round(reel_box.size.Z, 3), REEL_T)
record("portal.diameter", close(PORTAL_D, 44.0), PORTAL_D, 44.0)
record("portal.offset", close(PORTAL_Y, 31.0), PORTAL_Y, 31.0)
record("spindle.derived", close(SPINDLE_D, 7.2), SPINDLE_D, 7.2)
record("spindle.radial_clearance", close((SPINDLE_BORE_D - SPINDLE_D) / 2, 0.3), (SPINDLE_BORE_D - SPINDLE_D) / 2, 0.3)
record("axial.gap", close(AXIAL_GAP, 0.3), AXIAL_GAP, 0.3)
record("frame.height", FRAME_TOP_Y - FRAME_BOTTOM_Y <= 130, FRAME_TOP_Y - FRAME_BOTTOM_Y, "<=130")
record("stand.deploy_rotation_deg", close(STAND_DEPLOY_DEG, 112.0), STAND_DEPLOY_DEG, 112.0)
assembly_box = assembly.bounding_box()
record("assembly.deployed_depth_mm", 81.0 <= assembly_box.size.Y <= 83.0, round(assembly_box.size.Y, 3), "81.0..83.0")
record("part.count", len(parts) == 4, len(parts), 4)

result = {
    "schema_version": 1,
    "kind": "lantern-menagerie.spec-audit",
    "ok": all(row["passed"] for row in checks),
    "parameters": parameter_audit(),
    "checks": checks,
}
print(json.dumps(result, sort_keys=True, separators=(",", ":")))
raise SystemExit(0 if result["ok"] else 1)
