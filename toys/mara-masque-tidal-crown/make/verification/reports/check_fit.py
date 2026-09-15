"""Algebraic local fit audit, separate from BREP and mesh gates."""
import sys,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tidal_lib import CELL,BASE_D,BLACK_WIDTH,BLACK_RADIUS,HEIGHTS
assert CELL-BASE_D>=4
assert 2*(math.sqrt(2)*(BLACK_WIDTH/2-BLACK_RADIUS)+BLACK_RADIUS)<=BASE_D
assert min(HEIGHTS.values())>=12 and max(HEIGHTS.values())<=28
print('PASS: spacing, black circumscribed base, role heights; no hardware or retained joints')
