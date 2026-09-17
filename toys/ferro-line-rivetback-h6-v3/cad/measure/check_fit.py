"""Local fit ledger audit; geometry soundness remains with CAD gates."""

import json
import sys
from pathlib import Path

project = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project))
from params import *

checks = {
    "small_peg_per_side_clearance": (small_socket - small_peg) / 2,
    "hip_key_per_side_clearance": (hip_socket - hip_peg) / 2,
    "tenon_width_per_side_clearance": (tenon_socket_width - tenon_width) / 2,
    "tenon_height_per_side_clearance": (tenon_socket_height - tenon_height) / 2,
    "pin_per_side_clearance": (pin_hole - pin_diameter) / 2,
}
assert 0.15 <= checks["small_peg_per_side_clearance"] <= 0.30
assert 0.20 <= checks["hip_key_per_side_clearance"] <= 0.35
assert 0.20 <= checks["tenon_width_per_side_clearance"] <= 0.35
assert 0.20 <= checks["tenon_height_per_side_clearance"] <= 0.35
assert 0.15 <= checks["pin_per_side_clearance"] <= 0.30
print(json.dumps({"ok": True, "checks": checks}, sort_keys=True))
