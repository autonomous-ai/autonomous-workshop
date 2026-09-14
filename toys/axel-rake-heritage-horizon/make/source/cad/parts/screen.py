"""Touring panel; coplanar rear tongue supports a flat rear-face print."""
from math import hypot
from build123d import *
from params import *
from features.common import box_bounds

def panel_plane():
    length=hypot(COCKPIT_SCREEN_RISE,COCKPIT_SCREEN_SWEEP)
    return Plane(origin=COCKPIT_SCREEN_ORIGIN,x_dir=(0,1,0),z_dir=(COCKPIT_SCREEN_RISE/length,0,COCKPIT_SCREEN_SWEEP/length))

def build():
    length=hypot(COCKPIT_SCREEN_RISE,COCKPIT_SCREEN_SWEEP)
    lower,upper=COCKPIT_SCREEN_WIDTHS
    plane=panel_plane()
    outline=Polygon((-lower/2,0),(lower/2,0),(upper/2,length),(-upper/2,length),align=None)
    panel=extrude(plane*outline,amount=COCKPIT_SCREEN_THICKNESS)
    tongue=extrude(plane*Polygon((-COCKPIT_TONGUE_WIDTH/2,-COCKPIT_TONGUE_LENGTH),(COCKPIT_TONGUE_WIDTH/2,-COCKPIT_TONGUE_LENGTH),(COCKPIT_TONGUE_WIDTH/2,0),(-COCKPIT_TONGUE_WIDTH/2,0),align=None),amount=COCKPIT_TONGUE_THICKNESS)
    clipped=panel.fuse(tongue).intersect(box_bounds(COCKPIT_SCREEN_CLIP))
    assert len(clipped)==1, 'Screen must remain a single contiguous panel'
    return clipped[0]

def print_shape():
    return panel_plane().to_local_coords(build())
