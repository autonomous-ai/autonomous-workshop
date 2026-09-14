from build123d import Pos, Rot
from moon_lib import leaf
PRINTABLE = True
def gen_step():
    return Pos(0,0,7.4)*Rot(180,0,0)*leaf()
