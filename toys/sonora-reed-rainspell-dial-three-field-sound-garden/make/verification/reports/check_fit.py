#!/usr/bin/env python3
"""Project-specific connector and assembly-order audit."""

from __future__ import annotations

import math
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

import params as p  # noqa: E402


def main() -> int:
    checks = {
        "journal_diametral_clearance_mm": 2.0 * (p.WHEEL_BORE_RADIUS - p.JOURNAL_RADIUS),
        "guide_diametral_clearance_mm": 2.0 * (p.GUIDE_BORE_RADIUS - p.PLECTRUM_STEM_RADIUS),
        "guard_skirt_radial_clearance_mm": p.GUARD_INNER_RADIUS - p.WHEEL_SKIRT_OUTER_RADIUS,
        "guard_cage_radial_clearance_mm": p.GUARD_INNER_RADIUS - (p.FOLLOWER_CENTER_RADIUS + p.CAGE_RADIUS),
        "wheel_endplay_mm": p.CAP_SHOULDER_Z - p.WHEEL_HUB_TOP_Z,
        "keeper_cap_swept_clearance_mm": p.KEEPER_INNER_EDGE_RADIUS - p.CAP_SKIRT_RADII[1],
    }
    expected = {
        "journal_diametral_clearance_mm": 0.5,
        "guide_diametral_clearance_mm": 0.5,
        "guard_skirt_radial_clearance_mm": 0.8,
        "guard_cage_radial_clearance_mm": 1.8,
        "wheel_endplay_mm": 0.35,
        "keeper_cap_swept_clearance_mm": 0.5,
    }
    for key, value in checks.items():
        assert math.isclose(value, expected[key], abs_tol=1e-9), (key, value)
    connector_names = ("deck index seat", "journal", "follower guides", "keeper rails", "cap pockets")
    assembly_order = ("rib deck", "plectrum", "follower keeper", "wheel", "cap")
    assert len(set(connector_names)) == 5 and assembly_order[-1] == "cap"
    for key, value in checks.items():
        print(f"PASS {key}={value:.3f}")
    print("PASS connector naming and five-step assembly order declared")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
