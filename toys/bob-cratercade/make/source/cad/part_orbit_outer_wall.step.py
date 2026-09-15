"""One flat-base printed orbit outer wall."""
import params as p
from parts import orbit_wall
PRINTABLE=True

def gen_step():
    return orbit_wall.print_shape("outer")
