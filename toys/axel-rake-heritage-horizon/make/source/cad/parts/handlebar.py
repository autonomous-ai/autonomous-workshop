"""Planar swept touring bar with broad central adhesive land."""
from build123d import *
from params import *

def build():
    shape=Pos(0,0,COCKPIT_BAR_BOTTOM)*extrude(Polygon(*COCKPIT_BAR_OUTLINE,align=None),amount=COCKPIT_BAR_HEIGHT,dir=(0,0,1))
    return chamfer(shape.edges().group_by(Axis.Z)[-1],length=COCKPIT_BAR_CHAMFER)
