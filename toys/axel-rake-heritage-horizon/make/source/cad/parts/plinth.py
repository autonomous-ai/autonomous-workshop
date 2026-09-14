"""Removable gravity cradle; open-topped rectangular belly channel."""
from params import *
from features.common import box_bounds

def build():
    shape=box_bounds(COCKPIT_STAND_BASE)
    half=COCKPIT_STAND_POST_WIDTH/2
    outer=COCKPIT_STAND_OUTSIDE/2
    inner=COCKPIT_STAND_GAP/2
    for x in COCKPIT_STAND_POST_X:
        post=box_bounds((x-half,x+half,-outer,outer,0,COCKPIT_STAND_CONTACT_Z))
        for y0,y1 in ((-outer,-inner),(inner,outer)):
            post=post.fuse(box_bounds((x-half,x+half,y0,y1,COCKPIT_STAND_CONTACT_Z,COCKPIT_STAND_CONTACT_Z+COCKPIT_STAND_LIP_HEIGHT)))
        shape=shape.fuse(post)
    return shape
