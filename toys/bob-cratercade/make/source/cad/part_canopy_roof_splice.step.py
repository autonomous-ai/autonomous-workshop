"""One canopy roof splice in print pose."""
from build123d import Pos,Rot
import params as p
from parts.canopy_roof_splice import *
PRINTABLE=True
def gen_step():
    return Pos(0,0,p.CANOPY_FRAME_BOTTOM)*Rot(180,0,0)*build()
