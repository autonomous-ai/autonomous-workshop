"""Flat-print rear offset root and side-bolted column socket."""
from math import sqrt
from build123d import Plane,Pos,RegularPolygon,Rot,extrude
import params as p
from features.primitives import bounded_box,x_cylinder,z_cylinder,top_countersink


def build():
    x0,x1=p.CANOPY_POST_OUTER_X; y0,y1=p.CANOPY_POST_OUTER_Y
    dy=p.CANOPY_POST_ROOT_DY_REAR; r=p.CANOPY_ROOT_RING_OD/2
    bottom,top=p.CANOPY_POST_BASE_Z,p.CANOPY_REAR_ADAPTER_TOP
    shape=bounded_box(x0,x1,dy-r,y1,bottom,top)
    shape+=z_cylinder(p.CANOPY_POST_ROOT_X,dy,p.CANOPY_ROOT_RING_Z,bottom-p.CANOPY_ROOT_RING_Z,r)
    shape-=z_cylinder(p.CANOPY_POST_ROOT_X,dy,p.CANOPY_ROOT_RING_Z,p.CANOPY_ROOT_RING_T,p.M4_BORE/2)
    shape-=z_cylinder(p.CANOPY_POST_ROOT_X,dy,p.CANOPY_ROOT_RING_Z+p.CANOPY_ROOT_RING_T,top-p.CANOPY_ROOT_RING_Z-p.CANOPY_ROOT_RING_T,p.CANOPY_ROOT_TOOL_D/2)
    clear=p.CANOPY_REAR_SOCKET_CLEARANCE
    shape-=bounded_box(p.CANOPY_POST_CAP_PEG_X[0]-clear,p.CANOPY_POST_CAP_PEG_X[1]+clear,
                       p.CANOPY_POST_CAP_PEG_Y[0]-clear,p.CANOPY_POST_CAP_PEG_Y[1]+clear,
                       p.CANOPY_REAR_SOCKET_FLOOR,top)
    sx=p.CANOPY_SIDE_SHEET_X; half=p.CANOPY_PET_SLOT_W/2; z=bottom+p.CANOPY_SLOT_FLOOR
    shape-=bounded_box(sx-half,sx+half,dy-r,y0+p.CANOPY_SLOT_DEPTH,z,top)
    sy=p.CANOPY_END_PANEL_Y[1]
    shape-=bounded_box(x1-p.CANOPY_SLOT_DEPTH,x1,sy-half,sy+half,z,top)
    z=p.CANOPY_REAR_JOINT_Z
    shape-=x_cylinder(x0,x1-x0,p.M4_BORE/2,0,z)
    shape-=Pos(x0,0,z)*Rot(0,-90,0)*top_countersink(0,0,0,p.CSK_HEAD_MAX_H,p.M4_BORE,p.CSK_RECESS_D)
    profile=Plane.YZ*RegularPolygon(p.NUT_POCKET_AF/sqrt(3),6,rotation=30)
    shape-=Pos(p.CANOPY_POST_NUT_POCKET_X,0,z)*extrude(profile,amount=x1-p.CANOPY_POST_NUT_POCKET_X+p.CANOPY_CELL_GAP,dir=(1,0,0))
    assert len(shape.solids())==1
    return shape


def print_shape(right=False):
    shape=Pos(0,0,p.CANOPY_REAR_ADAPTER_TOP)*Rot(180,0,0)*build()
    return shape.mirror(Plane.YZ) if right else shape
