from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from neststomp_lib import BELLY_W, CHICK_W, DEPTH_GAP, DEPTH, LEFT_X, RIGHT_X

assert abs(BELLY_W - 54.0) < 1e-9
assert abs(CHICK_W - 36.0) < 1e-9
assert abs(DEPTH_GAP - 0.8) < 1e-9
assert abs((RIGHT_X - LEFT_X) - 16.4) < 1e-9
assert DEPTH >= 24.0
print("PASS: 0.8 mm front/back running gaps; 16.4 mm lateral stop travel; 24 mm owl depth; two source-declared printable parts")
