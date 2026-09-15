"""One canopy upright in inverted print pose."""
from build123d import Plane
from parts.canopy_post import print_shape
PRINTABLE=True
def gen_step():
    shape=print_shape(rear=True,end='rear')
    return shape.mirror(Plane.YZ) if True else shape
