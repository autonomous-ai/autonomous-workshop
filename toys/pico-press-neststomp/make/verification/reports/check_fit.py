from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from neststomp_lib import DEPTH, CHICK_DEPTH, DEPTH_GAP, BELLY_W, OWL_W, make_owl, make_chick

owl = make_owl()
chick = make_chick()
assert len(owl.solids()) == 1 and len(chick.solids()) == 1
assert abs(owl.bounding_box().min.Z) < 1e-6
assert abs(chick.bounding_box().min.Z) < 1e-6
assert abs(DEPTH_GAP - 0.8) < 1e-9
assert abs((OWL_W - BELLY_W) / 2.0 - 7.0) < 1e-9
assert DEPTH == 24.0 and CHICK_DEPTH == 22.4
print("PASS: two single-solid parts; both flat at Z=0; 0.8 mm face gaps; 7 mm chamber-side stops")
