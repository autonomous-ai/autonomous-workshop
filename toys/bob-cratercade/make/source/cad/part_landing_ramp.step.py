"""Upright landing ramp, including its flush-seated robust toe."""
from build123d import Pos
from parts.landing_ramp import build_ramp
import params as p
PRINTABLE=True

def gen_step():
    return Pos(0,0,p.RAMP_SEAT_DEPTH)*build_ramp()
