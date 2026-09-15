"""Lower roof frame, bottom face on bed and short stand-offs upward."""
from build123d import Pos
from parts.canopy_frame import build
import params as p
PRINTABLE=True

def gen_step():
    return Pos(0,0,-p.CANOPY_FRAME_BOTTOM)*build()
