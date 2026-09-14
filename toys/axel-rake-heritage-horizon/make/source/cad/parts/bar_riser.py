"""Separate swept riser prints on its planar side."""
from params import *
from features.common import prism_xz

def build():
    return prism_xz(COCKPIT_RISER_PROFILE,COCKPIT_RISER_Y,COCKPIT_RISER_WIDTH)
