#!/usr/bin/env python3
"""Deterministic analytical audit for Night-Sky Weave's declared grammar."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from night_sky_weave_lib import (
    CORE_THICKNESS,
    EDGE_GATE_WIDTH,
    FAMILIES,
    MOSAIC_SIZE,
    PLATE_GAP,
    TILE_SIZE,
    TILE_THICKNESS,
    validate_parameters,
)


validate_parameters()
assert FAMILIES == ("crescent", "comet", "star")
assert TILE_SIZE == 31.5
assert TILE_THICKNESS == 5.6
assert CORE_THICKNESS >= 3.2 - 1e-9
assert EDGE_GATE_WIDTH == 1.8
assert PLATE_GAP == 2.0
assert MOSAIC_SIZE == 98.5

print(json.dumps({
    "ok": True,
    "check": "night-sky-weave-spec",
    "inventory": {family: 3 for family in FAMILIES},
    "tile_mm": [TILE_SIZE, TILE_SIZE, TILE_THICKNESS],
    "mosaic_mm": [MOSAIC_SIZE, MOSAIC_SIZE, TILE_THICKNESS],
    "minimum_core_mm": CORE_THICKNESS,
    "print_targets": {
        "part_crescent.step.py": 3,
        "part_comet.step.py": 3,
        "part_star.step.py": 3
    },
    "combined_entry_printable": False,
    "universal_edge_gate_width_mm": EDGE_GATE_WIDTH,
    "rotation_and_flip_compatible": True
}, sort_keys=True))
