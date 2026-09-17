"""Monolithic bell-crank wings, mirrored at the hinge datum; print top-down."""
from build123d import *
import params as p
from features.primitives import axial_y, finish


def wing(side=1):
    root=Pos(0,p.HUB_Y0,0)*extrude(Plane.XZ*Polygon(*p.WING_ROOT_PROFILE,align=None),amount=p.HUB_Y1-p.HUB_Y0,dir=(0,1,0))
    blade=Pos(0,0,p.WING_TOP-p.WING_T)*extrude(Polygon(*p.WING_BLADE_OUTLINE,align=None),amount=p.WING_T,dir=(0,0,1))
    raw=root+blade
    raw=raw-[axial_y(p.HINGE_BORE/2,p.WING_BORE_Y0,p.WING_BORE_Y1),axial_y(p.DRIVE_BORE/2,p.WING_BORE_Y0,p.WING_BORE_Y1,-p.INPUT_ARM)]
    if side<0:
        raw=raw.mirror(Plane.YZ)
    return finish(raw,'wing_right' if side>0 else 'wing_left',p.VIOLET)
