#!/usr/bin/env python3
"""Deterministic STL support-angle screen for every Comet Heist print family.

This is deliberately not a slicer. It identifies downward facets steeper than
the declared self-support angle, excludes only faces lying on the build plate,
and verifies that the authored support plan covers every fresh family STL.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
from pathlib import Path

import numpy as np

PROJECT = Path(__file__).resolve().parents[1]
ANGLE_DEG = 45.0
LAYER_MM = 0.20
BED_TOLERANCE_MM = 0.01
AREA_TOLERANCE_MM2 = 0.50

SUPPORT_PLAN = {
    "part_comet_orbit.stl": "none",
    "part_comet_sun.stl": "none",
    "part_gate_bridge.stl": "generated-support-everywhere",
    "part_gate_keeper.stl": "none",
    "part_gravity_blade.stl": "generated-support-everywhere",
    "part_ready_spent_magazine.stl": "generated-support-everywhere",
    "part_seam_storage_key.stl": "none",
    "part_tray_a.stl": "generated-support-everywhere",
    "part_tray_b.stl": "generated-support-everywhere",
}


def load_stl(path: Path) -> np.ndarray:
    with path.open("rb") as handle:
        head = handle.read(84)
        if head[:5] == b"solid" and b"facet" in handle.read(512):
            handle.seek(0)
            vertices = [
                [float(value) for value in line.split()[1:4]]
                for line in handle.read().decode("utf-8", "replace").splitlines()
                if line.strip().startswith("vertex")
            ]
            return np.asarray(vertices, dtype=np.float64).reshape(-1, 3, 3)
        count = struct.unpack("<I", head[80:84])[0]
        payload = np.frombuffer(handle.read(count * 50), dtype=np.uint8)
    if payload.size != count * 50:
        raise ValueError(f"truncated STL: {path}")
    triangles = payload.reshape(count, 50)[:, 12:48].copy().view("<f4")
    return triangles.reshape(count, 3, 3).astype(np.float64)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect(path: Path) -> dict:
    triangles = load_stl(path)
    cross = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
    lengths = np.linalg.norm(cross, axis=1)
    normals = np.divide(cross, lengths[:, None], out=np.zeros_like(cross), where=lengths[:, None] > 0)
    area = lengths / 2.0
    above_bed = triangles[:, :, 2].max(axis=1) > BED_TOLERANCE_MM
    downward_limit = -math.cos(math.radians(ANGLE_DEG))
    critical = above_bed & (normals[:, 2] < downward_limit)
    critical_area = float(area[critical].sum())
    bbox = np.ptp(triangles.reshape(-1, 3), axis=0)
    mode = SUPPORT_PLAN[path.name]
    expected_support = mode != "none"
    observed_support = critical_area > AREA_TOLERANCE_MM2
    return {
        "path": path.name,
        "sha256": sha256(path),
        "triangle_count": int(len(triangles)),
        "envelope_mm": [round(float(value), 3) for value in bbox],
        "support_mode": mode,
        "critical_downward_triangle_count": int(critical.sum()),
        "critical_downward_area_mm2": round(critical_area, 3),
        "critical_z_range_mm": (
            [
                round(float(triangles[critical, :, 2].min()), 3),
                round(float(triangles[critical, :, 2].max()), 3),
            ]
            if critical.any()
            else None
        ),
        "support_plan_matches_geometry": expected_support == observed_support,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", default="measure/support-angle.json")
    args = parser.parse_args()
    observed = {path.name for path in PROJECT.glob("part_*.stl")}
    expected = set(SUPPORT_PLAN)
    rows = [inspect(PROJECT / name) for name in sorted(expected & observed)]
    by_name = {row["path"]: row for row in rows}
    blade = by_name.get("part_gravity_blade.stl", {})
    blade_entry = PROJECT / "part_gravity_blade.step.py"
    blade_source = blade_entry.read_text(encoding="utf-8")
    tray_a = by_name.get("part_tray_a.stl", {})
    tray_b = by_name.get("part_tray_b.stl", {})
    magazine = by_name.get("part_ready_spent_magazine.stl", {})
    tests = {
        "exact_family_coverage": observed == expected and len(rows) == 9,
        "support_plan_matches_all_fresh_meshes": all(row["support_plan_matches_geometry"] for row in rows),
        "gravity_blade_low_profile_with_vertical_trunnions": (
            "on_bed(build_blade(), (0, 90, 0))" in blade_source
            and blade.get("support_mode") == "generated-support-everywhere"
            and blade.get("critical_downward_area_mm2", 0) > AREA_TOLERANCE_MM2
            and blade.get("envelope_mm", [0, 0, 0])[2] < 16.0
            and max(blade.get("envelope_mm", [0, 0, 0])[:2]) > 35.0
        ),
        "tray_retention_lips_exposed_by_screen": all(
            row.get("critical_z_range_mm") is not None
            and row["critical_z_range_mm"][1] >= 18.0
            for row in (tray_a, tray_b)
        ),
        "magazine_tongue_exposed_by_screen": (
            magazine.get("critical_z_range_mm") is not None
            and magazine["critical_z_range_mm"][1] >= 12.0
        ),
    }
    report = {
        "schema_version": 1,
        "kind": "comet-heist.support-angle-screen",
        "method": {
            "angle_from_horizontal_deg": ANGLE_DEG,
            "nominal_layer_mm": LAYER_MM,
            "bed_face_tolerance_mm": BED_TOLERANCE_MM,
            "critical_area_tolerance_mm2": AREA_TOLERANCE_MM2,
            "description": "Downward STL facets whose surface is less than 45 degrees above horizontal are accumulated unless they lie on the build plate.",
        },
        "passed": all(tests.values()),
        "tests": tests,
        "gravity_blade_entry": {
            "path": blade_entry.name,
            "sha256": sha256(blade_entry),
            "rotation_y_deg": 90,
            "panel_support_reason": "The coaxial trunnion projects 3.35 mm beyond each broad blade face; with the trunnion vertical, the lower end contacts the bed and the parallel panel requires generated support.",
        },
        "families": rows,
        "limitations": [
            "This triangle-normal screen is support-angle evidence, not a slicer run or generated toolpath.",
            "The declared support mode does not prove support accessibility, surface quality, material behavior, dimensional accuracy, or a successful print.",
            "Physical printing, fit, friction, oscillation, impact retention, wear, handling, and durability remain unverified.",
        ],
    }
    report_path = PROJECT / args.report
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
