"""Printable side perimeter with its exact canopy post root pattern."""
import params as p
from parts import perimeter_wall
PRINTABLE=True
def gen_step():
    return perimeter_wall.print_shape(p.PERIMETER_LENGTHS[2],p.PERIMETER_SIDE_BOLTS[2],mirror=False,post_y=p.CANOPY_WALL_POST_Y[2])
