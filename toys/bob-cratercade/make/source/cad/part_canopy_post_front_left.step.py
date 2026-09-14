"""One canopy upright in inverted print pose."""
from build123d import Plane
from parts.canopy_post import print_shape
PRINTABLE=True
def gen_step():
    shape=print_shape(rear=False,end='front')
    return shape.mirror(Plane.YZ) if False else shape
