"""One flat-base printed orbit inner wall."""
import params as p
from parts import orbit_wall
PRINTABLE=True

def gen_step():
    return orbit_wall.print_shape("inner")
