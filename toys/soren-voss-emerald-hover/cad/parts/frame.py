"""One open rib frame with square guide and roofed shaft/shoulder bores."""
from build123d import *
import params as p
from features.primitives import box_at,axial_y,finish
from features.prisms import yz_prism,xz_prism,roof_x,roof_y,rectangular_loft

def frame():
    base=box_at(*p.BASE_BOUNDS)
    base=fillet(base.edges().filter_by(Axis.Z),radius=p.BASE_CORNER_R)
    raw=base+box_at(*p.MAST_BOUNDS)+yz_prism(p.SUPPORT_YZ,*p.SUPPORT_X)
    raw=raw+rectangular_loft(p.FAN_SECTIONS)+box_at(*p.BRIDGE_BOUNDS)
    raw=raw+rectangular_loft(p.PEDESTAL_SECTIONS)+box_at(*p.PEDESTAL_BOUNDS)
    for side in (-1,1):
        raw=raw+box_at(side*p.HINGE_X-p.BOSS_HALF_X,side*p.HINGE_X+p.BOSS_HALF_X,p.BOSS_Y0,p.BOSS_Y1,p.BOSS_Z0,p.BOSS_Z1)
        raw=raw+box_at(side*p.TOWER_X-p.TOWER_HALF_X,side*p.TOWER_X+p.TOWER_HALF_X,-p.TOWER_HALF_Y,p.TOWER_HALF_Y,p.TOWER_Z0,p.TOWER_Z1)
    cuts=[box_at(-p.GUIDE_BORE/2,p.GUIDE_BORE/2,-p.GUIDE_BORE/2,p.GUIDE_BORE/2,*p.GUIDE_CUT_Z)]
    for side in (-1,1):
        cuts += [roof_x(p.SHAFT_BORE/2,side*p.TOWER_X-p.TOWER_HALF_X-p.CUT_EXTENSION,side*p.TOWER_X+p.TOWER_HALF_X+p.CUT_EXTENSION,0,p.SHAFT_Z),roof_y(p.HINGE_FRAME_BORE/2,*p.HINGE_FRAME_CUT_Y,side*p.HINGE_X,p.HINGE_Z)]
        cuts += [axial_y(p.HEAD_ACCESS_R,p.HEAD_ACCESS_Y0,p.HEAD_ACCESS_Y1,side*p.HINGE_X,p.HINGE_Z)+box_at(side*p.HINGE_X-p.HEAD_ACCESS_R,side*p.HINGE_X+p.HEAD_ACCESS_R,p.HEAD_ACCESS_Y0,p.HEAD_ACCESS_Y1,p.HINGE_Z,p.HEAD_ACCESS_TOP)]
    cuts += [yz_prism(p.FRAME_SIDE_WINDOW_YZ,*p.FRAME_SIDE_WINDOW_X),xz_prism(p.FRAME_LOWER_WINDOW_XZ,*p.FRAME_LOWER_WINDOW_Y),xz_prism(p.FRAME_UPPER_WINDOW_XZ,*p.FRAME_UPPER_WINDOW_Y),box_at(*p.DRIVE_HEAD_CLEARANCE),xz_prism(p.GUIDE_FRONT_RELIEF_XZ,*p.GUIDE_FRONT_RELIEF_Y)]
    return finish(raw-cuts,'open_brass_frame',p.BRASS)
