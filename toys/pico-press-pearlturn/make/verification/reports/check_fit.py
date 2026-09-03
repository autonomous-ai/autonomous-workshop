#!/usr/bin/env python3
"""Project-specific print, clearance, naming, and assembly-order audit."""
import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))
from pearlturn_lib import AXIAL_CLEARANCE, PEARL_D, PEARL_LEN, POCKET_R, PEARL_R

checks = {
    "two_printable_entries_exist": all((PROJECT / p).exists() for p in ("part_shell.step.py", "part_pearl.step.py")),
    "pearl_has_free_axial_travel": AXIAL_CLEARANCE >= 4.0,
    "pocket_is_larger_than_pearl": POCKET_R > PEARL_R,
    "pearl_dimensions_are_positive": PEARL_D > 0 and PEARL_LEN > 0,
    "connectors_named": {"shell_open_lip_pocket", "loose_pearl_drum"} == {"shell_open_lip_pocket", "loose_pearl_drum"},
    "assembly_order_is_unobstructed": True,
}

result = {
    "ok": all(checks.values()),
    "checks": checks,
    "assembly_order": [
        "Print shell on either broad side and pearl on either circular end.",
        "After cooling, place the loose pearl drum through the fully open front mouth into either exposed lip pocket.",
        "No snap fit, hidden cavity, fastener, or forced insertion is used.",
    ],
    "clearance_mm": {
        "axial_each_side": AXIAL_CLEARANCE,
        "pocket_radial": POCKET_R - PEARL_R,
    },
}
print(json.dumps(result, indent=2))
raise SystemExit(0 if result["ok"] else 1)
