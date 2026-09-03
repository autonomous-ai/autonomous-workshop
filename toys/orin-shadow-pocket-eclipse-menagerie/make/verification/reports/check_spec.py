#!/usr/bin/env python3
"""Fast authored dimensional/spec audit; geometry gates own topology."""
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
src = (root / "pocket_eclipse.step.py").read_text()
required = ["SLAB = 4.0", "RELIEF = 2.0", "len(shape.solids()) == 1",
            "_owl_slab", "_rabbit_slab", "_fox_relief", "_crescent_relief"]
missing = [item for item in required if item not in src]
if missing:
    print({"ok": False, "missing": missing})
    sys.exit(1)
print({"ok": True, "slab_mm": 4.0, "one_piece_assertion": True,
       "projection_axes": ["+X owl", "+Y rabbit"]})

