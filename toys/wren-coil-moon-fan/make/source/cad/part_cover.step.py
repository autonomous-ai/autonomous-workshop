from build123d import Pos
from moon_lib import cover
PRINTABLE = True
def gen_step():
    return Pos(28.5,0,-2.05)*cover()
