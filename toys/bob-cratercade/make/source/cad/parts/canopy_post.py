"""Deck-rooted upright with a clear hex-key route and blind PET grooves."""
import math
from build123d import Plane,Pos,RegularPolygon,Rot,extrude
import params as p
from features.primitives import bounded_box,x_cylinder,yz_prism,z_cylinder,top_countersink


def root_offset(rear=False):
    return p.CANOPY_POST_ROOT_DY_REAR if rear else 0.0


def root_cutter(local_y):
    """Counterbore in a wall root, preserving its original six-mm lower land."""
    c=z_cylinder(p.CANOPY_POST_ROOT_X,local_y,0,p.PLAYFIELD_WALL_H,p.M4_BORE/2)
    c+=z_cylinder(p.CANOPY_POST_ROOT_X,local_y,p.CANOPY_ROOT_RING_Z,
                  p.PLAYFIELD_WALL_H-p.CANOPY_ROOT_RING_Z,p.CANOPY_ROOT_COUNTERBORE_D/2)
    return c


def build(rear=False,end='none'):
    assert end in ('none','front','rear')
    x0,x1=p.CANOPY_POST_OUTER_X; y0,y1=p.CANOPY_POST_OUTER_Y
    bottom,top=p.CANOPY_POST_BASE_Z,p.CANOPY_POST_TOP_Z+p.CANOPY_ROOF_LIFT
    body=bounded_box(x0,x1,y0,y1,bottom,top)
    body-=bounded_box(*p.CANOPY_POST_INNER_X,*p.CANOPY_POST_VOID_Y,bottom,top)
    dy=root_offset(rear); r=p.CANOPY_ROOT_RING_OD/2
    body+=bounded_box(x0,x1,min(y0,dy-r),y1,bottom,bottom+p.CANOPY_POST_BRACE_T)
    if rear:
        # The column seats into a separately printed, bolted offset adapter.
        body=body & bounded_box(x0,x1,y0,y1,p.CANOPY_REAR_ADAPTER_TOP,top)
        body+=bounded_box(x0,x1,y0,y1,p.CANOPY_REAR_ADAPTER_TOP,p.CANOPY_REAR_ADAPTER_TOP+p.CANOPY_POST_BRACE_T)
        body+=bounded_box(*p.CANOPY_POST_CAP_PEG_X,*p.CANOPY_POST_CAP_PEG_Y,
                           p.CANOPY_REAR_PEG_BOTTOM,p.CANOPY_REAR_ADAPTER_TOP)
        body-=x_cylinder(p.CANOPY_POST_CAP_PEG_X[0],p.CANOPY_POST_CAP_PEG_X[1]-p.CANOPY_POST_CAP_PEG_X[0],
                          p.M4_BORE/2,0,p.CANOPY_REAR_JOINT_Z)
    else:
        body+=z_cylinder(p.CANOPY_POST_ROOT_X,dy,p.CANOPY_ROOT_RING_Z,bottom-p.CANOPY_ROOT_RING_Z,r)
        body-=z_cylinder(p.CANOPY_POST_ROOT_X,dy,p.CANOPY_ROOT_RING_Z,p.CANOPY_ROOT_RING_T,p.M4_BORE/2)
        body-=z_cylinder(p.CANOPY_POST_ROOT_X,dy,p.CANOPY_ROOT_RING_Z+p.CANOPY_ROOT_RING_T,
                         top-p.CANOPY_ROOT_RING_Z-p.CANOPY_ROOT_RING_T,p.CANOPY_ROOT_TOOL_D/2)
    slot_bottom=p.CANOPY_REAR_ADAPTER_TOP if rear else bottom+p.CANOPY_SLOT_FLOOR
    sx=p.CANOPY_SIDE_SHEET_X; half=p.CANOPY_PET_SLOT_W/2
    for lo,hi in ((y0,y0+p.CANOPY_SLOT_DEPTH),(y1-p.CANOPY_SLOT_DEPTH,y1)):
        body-=bounded_box(sx-half,sx+half,lo,hi,slot_bottom,top)
    if end!='none':
        sy=(y0+y0+p.CANOPY_SLOT_DEPTH)/2 if end=='front' else (y1-p.CANOPY_SLOT_DEPTH+y1)/2
        body-=bounded_box(x1-p.CANOPY_SLOT_DEPTH,x1,sy-half,sy+half,slot_bottom,top)
    z=p.CANOPY_POST_CROSS_BOLT_Z+p.CANOPY_ROOF_LIFT
    body-=x_cylinder(x0,x1-x0,p.M4_BORE/2,0,z)
    body-=Pos(x0,0,z)*Rot(0,-90,0)*top_countersink(0,0,0,p.CSK_HEAD_MAX_H,p.M4_BORE,p.CSK_RECESS_D)
    profile=Plane.YZ*RegularPolygon(p.NUT_POCKET_AF/math.sqrt(3),6,rotation=30)
    body-=Pos(p.CANOPY_POST_NUT_POCKET_X,0,z)*extrude(profile,
              amount=x1-p.CANOPY_POST_NUT_POCKET_X+p.CANOPY_CELL_GAP,dir=(1,0,0))
    assert len(body.solids())==1
    return body


def print_shape(rear=False,end='none'):
    return Pos(0,0,p.CANOPY_POST_TOP_Z+p.CANOPY_ROOF_LIFT)*Rot(180,0,0)*build(rear,end)
