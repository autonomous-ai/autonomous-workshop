"""One common bucket/flag print, flat continuous lower datum on the bed."""
from build123d import Pos
from parts.jackpot_rocker import build_rocker
import params as p
PRINTABLE=True

def gen_step():
    return Pos(0,0,-p.ROCKER_PRINT_BASE_Z)*build_rocker()
