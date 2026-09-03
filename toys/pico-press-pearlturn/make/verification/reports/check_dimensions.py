from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pearlturn_lib import *

facts = {
    "shell_width_mm": SHELL_W,
    "shell_depth_mm": SHELL_D,
    "pearl_diameter_mm": PEARL_D,
    "pearl_length_mm": PEARL_LEN,
    "axial_clearance_each_side_mm": AXIAL_CLEARANCE,
    "pocket_radial_clearance_mm": POCKET_R - PEARL_R,
    "vault_angle_degrees": VAULT_DEG,
    "printed_parts": 2,
}
assert facts["axial_clearance_each_side_mm"] >= 2.0
assert facts["pocket_radial_clearance_mm"] >= 0.6
assert facts["printed_parts"] == 2
print(json.dumps({"ok": True, "facts": facts}, indent=2))
