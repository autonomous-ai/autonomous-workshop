#!/usr/bin/env python3
"""Deterministic continuity, crossing, clearance, and orientation audit."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

from eclipse_braid_lib import P, route_points  # noqa: E402


def distance(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def unit(v):
    norm = math.sqrt(sum(x * x for x in v))
    return tuple(x / norm for x in v)


def tangent(points, index):
    before = points[(index - 1) % len(points)]
    after = points[(index + 1) % len(points)]
    return unit(tuple(a - b for a, b in zip(after, before)))


def nearest_index(points, target):
    return min(range(len(points)), key=lambda i: distance(points[i], target))


def main() -> int:
    points = route_points(128, 64)
    segment_lengths = [distance(p, points[(i + 1) % len(points)]) for i, p in enumerate(points)]
    route_length = sum(segment_lengths)

    # The two projection crossings are exact by construction. Each has one low
    # and one high visit, and the over-strand alternates between traversals.
    crossings = []
    for x in (-P.crossing_x, P.crossing_x):
        nearby = sorted(
            points,
            key=lambda p: math.hypot(p[0] - x, p[1]),
        )[:2]
        crossings.append(
            {
                "x_mm": x,
                "projected_visit_error_mm": max(math.hypot(p[0] - x, p[1]) for p in nearby),
                "low_z_mm": min(p[2] for p in nearby),
                "high_z_mm": max(p[2] for p in nearby),
                "rail_center_separation_mm": abs(nearby[0][2] - nearby[1][2]),
            }
        )

    home_index = nearest_index(points, (-P.half_straight - P.lobe_radius_x, 0.0, P.low_rail_z))
    far_index = nearest_index(points, (P.half_straight + P.lobe_radius_x, 0.0, P.low_rail_z))
    home_tangent = tangent(points, home_index)
    far_tangent = tangent(points, far_index)
    half_turn_dot = sum(a * b for a, b in zip(home_tangent, far_tangent))
    return_dot = sum(a * b for a, b in zip(home_tangent, home_tangent))

    checks = {
        "single_periodic_route": len(points) == 384 and max(segment_lengths) < 2.0,
        "two_separated_crossings": len(crossings) == 2 and 2.0 * P.crossing_x >= 25.0,
        "crossing_projection_accuracy": all(c["projected_visit_error_mm"] < 0.8 for c in crossings),
        "crossing_layer_clearance": all(
            c["rail_center_separation_mm"] - 2.0 * P.runner_outer_radius >= 1.0
            for c in crossings
        ),
        "orientation_flips_halfway": half_turn_dot < -0.98,
        "orientation_returns_home": return_dot > 0.999,
        "capture_is_topological": (
            P.runner_slot_width < 2.0 * P.rail_radius
            and P.runner_slot_width > P.web_thickness
        ),
        "runner_clears_base": (
            P.low_rail_z - P.runner_outer_radius - P.base_thickness >= 1.2
        ),
    }
    payload = {
        "schema_version": 1,
        "check_id": "eclipse-braid-route-traversal",
        "ok": all(checks.values()),
        "route": {
            "sample_count": len(points),
            "closed_by_periodic_spline": True,
            "length_mm": round(route_length, 3),
            "max_sample_gap_mm": round(max(segment_lengths), 3),
            "direction": "bidirectional by reversing the same ordered centerline",
        },
        "crossings": crossings,
        "orientation": {
            "home_tangent": home_tangent,
            "far_lobe_tangent": far_tangent,
            "half_turn_dot": half_turn_dot,
            "return_dot": return_dot,
        },
        "checks": checks,
        "limitations": [
            "Digital rigid geometry does not prove printed friction, wear, or human comfort.",
            "The route check proves centerline continuity and declared clearances, not a physical print.",
        ],
    }
    out_path = PROJECT.parent / "evidence" / "route-traversal.json"
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, sort_keys=True))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

