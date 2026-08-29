#!/usr/bin/env python3
"""Deterministic layout audit for the non-overlapping three-by-three plate."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from night_sky_weave_lib import MOSAIC_SIZE, PITCH, PLATE_GAP, TILE_SIZE


centers = [((column - 1) * PITCH, (1 - row) * PITCH) for row in range(3) for column in range(3)]
for index, first in enumerate(centers):
    for second in centers[index + 1:]:
        dx = abs(first[0] - second[0])
        dy = abs(first[1] - second[1])
        if dx < PITCH and dy < PITCH:
            raise AssertionError("tile envelopes overlap")

assert PITCH - TILE_SIZE == PLATE_GAP == 2.0
assert MOSAIC_SIZE < 100.0

print(json.dumps({
    "ok": True,
    "check": "night-sky-weave-layout",
    "tile_count": len(centers),
    "minimum_xy_gap_mm": PLATE_GAP,
    "mosaic_envelope_mm": [MOSAIC_SIZE, MOSAIC_SIZE],
    "fits_under_100_mm_square": True
}, sort_keys=True))
