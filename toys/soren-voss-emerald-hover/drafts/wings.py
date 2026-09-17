"""Monolithic bell-crank wings, mirrored at the hinge datum; print top-down."""
from build123d import *
import params as p
from features.primitives import axial_y, finish

ROOT_PROFILE=((-2,7.6),(8,7.6),(6,6),(4.5,0),(3.3,-3.3),(0,-4.5),(-3.3,-3.3),(-9,-1.7),(-9,1.7))
BLADE_OUTLINE=((6,-4),(8,1),(14,2),(22,0),(30,-4),(38,-10),(37.5,-11.5),(29,-10.5),(28,-9.5),(23,-10),(22,-8.5),(17,-8.5),(16,-7),(11,-7),(10,-5.5),(6,-5))

def wing(side=1):
    root=Pos(0,p.HUB_Y0,0)*extrude(Plane.XZ*Polygon(*ROOT_PROFILE,align=None),amount=p.HUB_Y1-p.HUB_Y0,dir=(0,1,0))
    blade=Pos(0,0,p.WING_TOP-p.WING_T)*extrude(Polygon(*BLADE_OUTLINE,align=None),amount=p.WING_T,dir=(0,0,1))
    raw=root+blade
    raw=raw-[axial_y(p.HINGE_BORE/2,-5,4),axial_y(p.DRIVE_BORE/2,-5,4,-p.INPUT_ARM)]
    if side<0:
        raw=raw.mirror(Plane.YZ)
    return finish(raw,'wing_right' if side>0 else 'wing_left',p.VIOLET)
