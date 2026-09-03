from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from build123d import Pos
from neststomp_lib import (BELLY_H, DEPTH_GAP, LEFT_X, RIGHT_X,
                           make_chick, make_owl)

owl = make_owl()
assert abs(owl.bounding_box().size.X - 68.0) < 1e-6
assert abs(owl.bounding_box().size.Y - 80.0) < 1e-6
assert abs(owl.bounding_box().size.Z - 24.0) < 1e-6

samples = 17
for i in range(samples):
    x = LEFT_X + (RIGHT_X - LEFT_X) * i / (samples - 1)
    chick = make_chick().moved(Pos(x, 0, DEPTH_GAP))
    overlap = (owl & chick).volume
    assert overlap < 0.001, (i, x, overlap)
    bb = chick.bounding_box()
    assert bb.min.X >= -27.0 - 1e-6 and bb.max.X <= 27.0 + 1e-6
    assert bb.max.Y <= BELLY_H + 1e-6

print(f"PASS: {samples} exact lateral samples span {RIGHT_X-LEFT_X:.1f} mm without solid overlap; endpoint wall clearance is 0.8 mm")
