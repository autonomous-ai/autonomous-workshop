"""One canopy end join rear in print pose."""
from build123d import Pos
import params as p
from parts.canopy_end_join import *
PRINTABLE=True
def gen_step():
    return print_shape(True)
