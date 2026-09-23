"""Algebraic interface ledger; generic gates own actual solid measurements."""
import math
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import seesaw_lib as p
assert abs((p.BORE_D-p.PIN_D)/2-0.4)<1e-8
assert abs((p.BODY_BORE_D-p.BODY_PIN_D)/2-0.4)<1e-8
assert abs(p.KEY_SLOT-p.KEY_T-0.4)<1e-8
assert p.SLIDE_FRONT-p.SKIN_BACK>=0.4-1e-8
assert p.COVER_FRONT-p.SLIDE_BACK>=0.4-1e-8
assert 15<=p.ANGLE<=20
assert 180<2*p.BEAM_HALF<210
q=p.DRIVE_H*math.sin(math.radians(p.ANGLE))
assert p.MASK_RIGHT-q < -56 # bull-up uncovers complete smile
assert p.MASK_LEFT+q < -56 and p.MASK_RIGHT+q > -42 # bull-down covers
assert p.TEAR_MASK_LEFT+q > 56 # bear-up uncovers both tears
assert p.TEAR_MASK_RIGHT-q > 56 and p.TEAR_MASK_LEFT-q <42
assert p.SLOT_Z0 < p.DRIVE_H*math.cos(math.radians(p.ANGLE))
assert p.SLOT_Z1 > p.DRIVE_H
print("PASS: shared fit equations and three-state aperture bounds; no motion or physical-fit verdict")
