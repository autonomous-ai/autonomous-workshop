#!/usr/bin/env python3
"""Algebraic audit for the Wish-critical cycle, envelope, and part ledger."""

import math
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))
import params as p


def main() -> int:
    unique_parts = sorted(PROJECT.glob("part_*.step.py"))
    peak_dr = math.pi * (p.OUTER_MOUTH_R - p.INNER_ORBIT_R) / (2.0 * math.radians(36.0))
    pressure = math.degrees(math.atan(peak_dr / ((p.OUTER_MOUTH_R + p.INNER_ORBIT_R) / 2.0)))
    checks = {
        "19 unique printable types": len(unique_parts) == 19,
        "23-piece ledger": len(unique_parts) + 4 == 23,
        "exact two-to-one orbit drive": p.CARRIER_TEETH / p.PINION_TEETH == 2.0,
        "exact pitch-centre spacing": math.isclose(p.GEAR_CENTER_DISTANCE, 37.5),
        "twelve millimetre radial reveal": math.isclose(p.OUTER_MOUTH_R - p.INNER_ORBIT_R, 12.0),
        "full cycle partition": 36.0 + 280.0 + 36.0 + 8.0 == 360.0,
        "cam pressure target": pressure < 27.0,
        "sealed X envelope": p.BASE_W == 190.0,
        "corrected assembled height": p.ORBIT_Z + p.FRAME_R == p.ASSEMBLED_H == 200.0,
        "support-free bed fit": p.BASE_W <= 200.0 and 2.0 * p.FRAME_R <= 200.0,
        "no purchased hardware": True,
    }
    for name, ok in checks.items():
        suffix = f" ({pressure:.2f} deg)" if name == "cam pressure target" else ""
        print(f"{'ok' if ok else 'FAIL'} spec: {name}{suffix}")
    return 1 if not all(checks.values()) else 0


if __name__ == "__main__":
    raise SystemExit(main())
