#!/usr/bin/env python3
"""Fast project-specific algebraic checks; geometry gates own solid validity."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

from eclipse_braid_lib import P  # noqa: E402


def main() -> int:
    checks = {
        "rail_radial_clearance_mm": P.runner_inner_radius - P.rail_radius,
        "web_side_clearance_mm": (P.runner_slot_width - P.web_thickness) / 2.0,
        "capture_overlap_per_side_mm": (2.0 * P.rail_radius - P.runner_slot_width) / 2.0,
        "base_runner_clearance_mm": P.low_rail_z - P.runner_outer_radius - P.base_thickness,
        "crossing_envelope_clearance_mm": (
            P.high_rail_z - P.low_rail_z - 2.0 * P.runner_outer_radius
        ),
        "crossing_separation_mm": 2.0 * P.crossing_x,
        "runner_wall_mm": P.runner_outer_radius - P.runner_inner_radius,
        "rail_diameter_mm": 2.0 * P.rail_radius,
    }
    thresholds = {
        "rail_radial_clearance_mm": 0.8,
        "web_side_clearance_mm": 0.4,
        "capture_overlap_per_side_mm": 0.8,
        "base_runner_clearance_mm": 1.2,
        "crossing_envelope_clearance_mm": 1.0,
        "crossing_separation_mm": 25.0,
        "runner_wall_mm": 2.0,
        "rail_diameter_mm": 4.0,
    }
    failed = [name for name, value in checks.items() if value < thresholds[name]]
    payload = {
        "ok": not failed,
        "checks": checks,
        "minimums": thresholds,
        "failed": failed,
    }
    print(json.dumps(payload, sort_keys=True))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())

