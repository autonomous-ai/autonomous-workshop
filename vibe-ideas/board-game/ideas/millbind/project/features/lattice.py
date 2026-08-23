"""The ONE 37-point triangular lattice generator for the whole project.

centre + ring of 6 + ring of 12 + ring of 18, at `pin_pitch` spacing --
generated exactly once here and reused for: yard_board's pin cutting, the
18-pin sill ring, the plank-rib layout, the assembly's supply-gear
placement, and fit_checks.py's pin-location lookups. Never regenerate this
trig a second time (per print_plan / lessons.md).
"""
from __future__ import annotations

import math

# Axial hex-grid unit directions (pointy-top layout), used to walk each ring.
_DIRECTIONS = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]


def hex_lattice_positions(pitch: float, max_ring: int = 3) -> list[tuple[float, float, int]]:
    """37-point triangular lattice: centre + rings of 6/12/18.

    Returns a list of (x, y, ring) so callers can pick out the 18 outer
    "yard pins" (ring == max_ring) that carry the raised sill, vs the 19
    inner pins that take supply gears only.
    """

    def axial_to_xy(q: int, r: int) -> tuple[float, float]:
        x = pitch * (q + r / 2.0)
        y = pitch * (r * math.sqrt(3) / 2.0)
        return (x, y)

    pts: list[tuple[float, float, int]] = [(0.0, 0.0, 0)]
    for k in range(1, max_ring + 1):
        q, r = _DIRECTIONS[4][0] * k, _DIRECTIONS[4][1] * k
        ring: list[tuple[int, int]] = []
        for i in range(6):
            for _ in range(k):
                ring.append((q, r))
                q += _DIRECTIONS[i][0]
                r += _DIRECTIONS[i][1]
        for (qq, rr) in ring:
            x, y = axial_to_xy(qq, rr)
            pts.append((x, y, k))
    return pts
