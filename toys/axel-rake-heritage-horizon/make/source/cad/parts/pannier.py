"""Paired chamfered touring luggage, outboard face on print bed."""
from build123d import *
from features.common import box_bounds
from params import (BODY_PANNIER_BOUNDS, BODY_PANNIER_CHAMFER,
    BODY_PANNIER_SEAM_BOUNDS, BODY_PANNIER_SOCKET_X,
    BODY_PANNIER_SOCKET_HALF_WIDTH, BODY_PANNIER_SOCKET_YZ_BOUNDS)

def build():
    bag=box_bounds(BODY_PANNIER_BOUNDS)
    # Retain the whole bed perimeter. Chamfer vertical corners and top only;
    # a nominal45-degree bed bevel produced unsupported first-layer growth.
    outer_y=BODY_PANNIER_BOUNDS[3]
    edges=[e for e in bag.edges() if e.center().Y < outer_y-1e-6]
    bag=chamfer(edges,length=BODY_PANNIER_CHAMFER)
    # Inboard lid seam opens upward during printing; bed face remains planar.
    bag=bag-box_bounds(BODY_PANNIER_SEAM_BOUNDS)
    # Open upward in print orientation: the two inboard mounting sockets.
    half=BODY_PANNIER_SOCKET_HALF_WIDTH
    for x in BODY_PANNIER_SOCKET_X:
        bag=bag-box_bounds((x-half,x+half,*BODY_PANNIER_SOCKET_YZ_BOUNDS))
    return bag
