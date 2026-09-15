"""Bearing frame with broad deck-contact face on the bed."""
from build123d import Pos
from parts.jackpot_frame import build_frame
import params as p
PRINTABLE=True

def gen_step():
    return Pos(0,0,p.JACKPOT_AXIS[2])*build_frame()
