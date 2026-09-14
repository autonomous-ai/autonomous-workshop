"""Positive-side broad tread, underside flat and upper perimeter chamfered."""
from build123d import *
from params import *
from features.common import box_bounds

def build():
    shape=box_bounds(COCKPIT_BOARD_BOUNDS)
    shape=fillet(shape.edges().filter_by(Axis.Z),radius=COCKPIT_BOARD_RADIUS)
    return chamfer(shape.edges().group_by(Axis.Z)[-1],length=COCKPIT_BOARD_CHAMFER)
