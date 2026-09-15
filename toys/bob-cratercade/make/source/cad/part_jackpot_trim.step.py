"""One reversible trim block, counterbored underside on the bed."""
from build123d import Pos
from parts.jackpot_trim import build_trim
import params as p
PRINTABLE=True

def gen_step():
    return Pos(0,0,p.TRIM_H/2)*build_trim()
