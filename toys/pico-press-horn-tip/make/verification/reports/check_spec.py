#!/usr/bin/env python3
"""Algebraic envelope and stability checks for Horn Tip. Does not rebuild solids."""

from __future__ import annotations

import math
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUTER_R = 42.0
INNER_R = 30.0
HALF_ANGLE_DEG = 50.0
THICKNESS = 18.0
HORN_R = (OUTER_R - INNER_R) / 2.0
MID_R = (OUTER_R + INNER_R) / 2.0


def annular_sector_com_radius() -> float:
    alpha = math.radians(HALF_ANGLE_DEG)
    return (
        (2.0 / 3.0)
        * (OUTER_R**3 - INNER_R**3)
        / (OUTER_R**2 - INNER_R**2)
        * (math.sin(alpha) / alpha)
    )


def main() -> int:
    assert math.isclose(HORN_R, 6.0)
    assert THICKNESS >= 16.0
    com_r = annular_sector_com_radius()
    if not 0.0 < com_r < OUTER_R:
        raise SystemExit(f"unstable rocker COM radius {com_r}")
    alpha = math.radians(HALF_ANGLE_DEG)
    span = 2.0 * (MID_R * math.sin(alpha) + HORN_R)
    horn_y = OUTER_R + MID_R * math.sin(math.radians(270.0) + alpha)
    height = horn_y + HORN_R
    if not 64.0 <= span <= 72.0:
        raise SystemExit(f"span {span} mm outside envelope")
    if not 22.0 <= height <= 28.0:
        raise SystemExit(f"height {height} mm outside envelope")
    print(
        f"check_spec: ok span={span:.2f} height={height:.2f} "
        f"thickness={THICKNESS:.1f} com_r={com_r:.2f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
