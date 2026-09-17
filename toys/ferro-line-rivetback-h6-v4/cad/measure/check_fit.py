"""Local fit ledger audit; geometry soundness remains with CAD gates."""

import json
import sys
from pathlib import Path

project = Path(__file__).resolve().parents[1]
workspace = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(workspace / ".agents" / "skills" / "cad" / "scripts"))
sys.path.insert(0, str(project))
from params import *

checks = {
    "carapace_peg_x_per_side_clearance": (small_socket - small_peg) / 2,
    "carapace_peg_y_per_side_clearance": (small_socket - small_peg * 0.72) / 2,
    "hip_key_z_per_side_clearance": (hip_socket - hip_peg) / 2,
    "hip_key_y_per_side_clearance": (hip_socket * 0.78 - hip_peg * 0.76) / 2,
    "hip_upper_tenon_y_per_side_clearance": (13.5 - 13.0) / 2,
    "hip_upper_tenon_z_per_side_clearance": (tenon_socket_height - tenon_height) / 2,
    "knee_lower_tenon_y_per_side_clearance": (lower_width + 0.5 - lower_width) / 2,
    "knee_lower_tenon_z_per_side_clearance": (tenon_socket_height - tenon_height) / 2,
    "dorsal_key_per_side_clearance": (dorsal_socket - dorsal_key) / 2,
    "foot_receiver_y_per_side_clearance": (7.5 - 7.0) / 2,
    "foot_receiver_z_per_side_clearance": (3.5 - 3.0) / 2,
    "foot_receiver_depth_clearance": 5.5 - 5.5,
    "pin_radial_per_side_clearance": (pin_hole - pin_diameter) / 2,
}
expected = {
    "carapace_peg_x_per_side_clearance": 0.20,
    "carapace_peg_y_per_side_clearance": 0.76,
    "hip_key_z_per_side_clearance": 0.25,
    "hip_key_y_per_side_clearance": 0.275,
    "hip_upper_tenon_y_per_side_clearance": 0.25,
    "hip_upper_tenon_z_per_side_clearance": 0.25,
    "knee_lower_tenon_y_per_side_clearance": 0.25,
    "knee_lower_tenon_z_per_side_clearance": 0.25,
    "dorsal_key_per_side_clearance": 0.25,
    "foot_receiver_y_per_side_clearance": 0.25,
    "foot_receiver_z_per_side_clearance": 0.25,
    "foot_receiver_depth_clearance": 0.0,
    "pin_radial_per_side_clearance": 0.20,
}
for name, expected_value in expected.items():
    assert abs(checks[name] - expected_value) < 1e-9, (name, checks[name], expected_value)
print(json.dumps({"ok": True, "checks": checks}, sort_keys=True))
