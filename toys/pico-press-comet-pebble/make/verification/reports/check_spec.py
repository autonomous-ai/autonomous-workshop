"""Narrow exact-source audit for Comet Pebble's envelope and one-piece contract."""

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "comet_pebble.step.py"
SPEC = importlib.util.spec_from_file_location("comet_pebble_entry", SOURCE)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
SHAPE = MODULE.gen_step()
BOX = SHAPE.bounding_box()
SIZE = BOX.size

checks = {
    "one_solid": len(SHAPE.solids()) == 1,
    "bed_z_zero": abs(BOX.min.Z) < 1e-6,
    "palm_size_x": 66.0 <= SIZE.X <= 70.0,
    "palm_size_y": 42.0 <= SIZE.Y <= 46.0,
    "palm_size_z": 32.0 <= SIZE.Z <= 36.0,
    "positive_volume": SHAPE.volume > 42000.0,
}
result = {
    "schema_version": 1,
    "check": "comet-pebble-spec",
    "ok": all(checks.values()),
    "checks": checks,
    "bbox_mm": [SIZE.X, SIZE.Y, SIZE.Z],
    "volume_mm3": SHAPE.volume,
}
print(json.dumps(result, sort_keys=True))
raise SystemExit(0 if result["ok"] else 2)
