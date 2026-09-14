"""One canopy post cap in print pose."""
from build123d import Pos
import params as p
from parts.canopy_post_cap import *
PRINTABLE=True
def gen_step():
    return print_shape()
