"""Upper roof clamp frame, underside down."""
from build123d import Pos
from parts.canopy_cap import build
import params as p
PRINTABLE=True

def gen_step():
    return Pos(0,0,-p.CANOPY_CAP_BOTTOM)*build()
