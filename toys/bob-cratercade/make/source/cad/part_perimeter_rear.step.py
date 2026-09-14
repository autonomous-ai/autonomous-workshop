"""One flat-base printed perimeter rear."""
import params as p
from parts import perimeter_wall
PRINTABLE=True

def gen_step():
    return perimeter_wall.print_shape(p.PERIMETER_REAR_LENGTH,p.PERIMETER_REAR_BOLTS)
