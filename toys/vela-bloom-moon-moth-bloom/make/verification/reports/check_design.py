#!/usr/bin/env python3
"""Deterministic geometry audit for the sealed Make-r0002 motion states."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from build123d import Pos, Rot

from moon_moth_bloom_lib import (
    BORE_D,
    DROP_Q,
    FLANGE_D,
    HIGH_UNDERSIDE,
    LOW_UNDERSIDE,
    MODULE,
    OPEN_Q,
    PAIR_BACKLASH,
    PITCH_R,
    PIVOT_X,
    PIVOT_Y,
    POST_D,
    RAISED_Z,
    SEATED_Z,
    SERVICE_Q,
    TEETH,
    WING_T,
    make_chassis,
    make_wing,
    placed_wing,
)


def _intersection_volume(a, b) -> float:
    return round(float((a & b).volume), 6)


def _placed_right(q: float, z: float, phase_delta: float):
    return Pos(PIVOT_X, PIVOT_Y, z) * Rot(0, 0, -q + phase_delta) * make_wing(1)


def _bounds(shape) -> list[float]:
    b = shape.bounding_box()
    return [
        round(b.min.X, 4), round(b.min.Y, 4), round(b.min.Z, 4),
        round(b.max.X, 4), round(b.max.Y, 4), round(b.max.Z, 4),
    ]


def audit() -> dict:
    chassis = make_chassis()
    printable = {
        "chassis": chassis,
        "left_wing_control": make_wing(-1),
        "right_wing": make_wing(1),
    }
    part_inventory = {
        name: {"solid_count": len(shape.solids()), "bounds_mm": _bounds(shape)}
        for name, shape in printable.items()
    }

    phase_delta = (PAIR_BACKLASH / PITCH_R) * 180.0 / 3.141592653589793 / 2.0
    service_q = [118, 94, 88, 84, 82, 78]
    operating_q = [82, 62, 41, 20, 18, 0]
    poses = []
    for q in service_q:
        z = RAISED_Z
        left = placed_wing(-1, q, z)
        for edge in (-phase_delta, phase_delta):
            right = _placed_right(q, z, edge)
            poses.append({
                "mode": "raised_service",
                "q_deg": q,
                "backlash_edge_deg": round(edge, 6),
                "z_mm": z,
                "chassis_left_overlap_mm3": _intersection_volume(chassis, left),
                "chassis_right_overlap_mm3": _intersection_volume(chassis, right),
                "wing_pair_overlap_mm3": _intersection_volume(left, right),
            })
    for q in operating_q:
        z = SEATED_Z
        left = placed_wing(-1, q, z)
        for edge in (-phase_delta, phase_delta):
            right = _placed_right(q, z, edge)
            poses.append({
                "mode": "seated_operating",
                "q_deg": q,
                "backlash_edge_deg": round(edge, 6),
                "z_mm": z,
                "chassis_left_overlap_mm3": _intersection_volume(chassis, left),
                "chassis_right_overlap_mm3": _intersection_volume(chassis, right),
                "wing_pair_overlap_mm3": _intersection_volume(left, right),
            })

    captured_lift_overlap = _intersection_volume(chassis, placed_wing(-1, 41, RAISED_Z))
    closed = chassis.fuse(placed_wing(-1, 0, SEATED_Z), placed_wing(1, 0, SEATED_Z))
    opened = chassis.fuse(placed_wing(-1, OPEN_Q, SEATED_Z), placed_wing(1, OPEN_Q, SEATED_Z))
    max_unintended = max(
        value
        for pose in poses
        for key, value in pose.items()
        if key.endswith("overlap_mm3")
    )
    passed = (
        len(printable) == 3
        and all(item["solid_count"] == 1 for item in part_inventory.values())
        and max_unintended <= 0.001
        and captured_lift_overlap > 0.001
    )
    return {
        "schema_version": 1,
        "kind": "moon-moth-bloom.geometry-audit",
        "passed": passed,
        "part_inventory": part_inventory,
        "gear": {
            "module_mm": MODULE,
            "teeth_each": TEETH,
            "pitch_radius_mm": PITCH_R,
            "axis_spacing_mm": 2 * PIVOT_X,
            "pair_backlash_mm": PAIR_BACKLASH,
            "sampled_phase_edges_deg": round(phase_delta, 6),
        },
        "capture": {
            "post_diameter_mm": POST_D,
            "bore_diameter_mm": BORE_D,
            "flange_diameter_mm": FLANGE_D,
            "raised_top_mm": RAISED_Z + WING_T,
            "service_hood_clearance_mm": HIGH_UNDERSIDE - (RAISED_Z + WING_T),
            "seated_top_mm": SEATED_Z + WING_T,
            "low_roof_clearance_mm": LOW_UNDERSIDE - (SEATED_Z + WING_T),
            "drop_q_deg": DROP_Q,
            "service_q_deg": SERVICE_Q,
            "captured_q41_lift_overlap_mm3": captured_lift_overlap,
        },
        "envelopes": {
            "closed_bounds_mm": _bounds(closed),
            "open_bounds_mm": _bounds(opened),
        },
        "max_unintended_overlap_mm3": max_unintended,
        "poses": poses,
        "limitations": [
            "No successful print or physical fit is claimed.",
            "CAD does not establish force, friction, wear, cycle life, or human response.",
            "Backlash poses are rigid geometric phase samples, not measured tooth play.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    result = audit()
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    Path(args.out).write_text(payload, encoding="utf-8")
    print(json.dumps({"ok": result["passed"], "sha256": hashlib.sha256(payload.encode()).hexdigest()}))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
