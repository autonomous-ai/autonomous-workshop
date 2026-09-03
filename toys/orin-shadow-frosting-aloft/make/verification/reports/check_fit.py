"""Project-specific algebraic audit for the two sliding guide channels."""
import pathlib
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import params

SLIP_DIAMETRAL_CLEARANCE_MM = 0.4
expected_gap = params.GUIDE_W + SLIP_DIAMETRAL_CLEARANCE_MM
actual_gap = params.GUIDE_W + 2 * params.SLIDE_CLEARANCE
assert abs(expected_gap - actual_gap) < 1e-9
assert params.CAP_BOTTOM < params.WRAPPER_HEIGHT < params.GUIDE_TOP
assert params.TRAVEL > 0
print("check_fit: ok - paired guide channels use slip clearance and span the 28 mm lift")
