"""Broad funnel and two bolted split collars; funnel prints rim-down."""
from build123d import Align,Axis,Circle,Cone,Pos,Rectangle,extrude,loft
import params as p
from features.primitives import bounded_box,z_cylinder,top_countersink

def outer_funnel():
    bottom=Circle(p.HOPPER_THROAT_ID/2+p.HOPPER_WALL)
    top=Pos(0,0,p.HOPPER_TOP_Z)*Rectangle(p.HOPPER_TOP_W,p.HOPPER_TOP_L)
    return loft([bottom,top])+z_cylinder(0,0,p.HOPPER_BOTTOM_Z,-p.HOPPER_BOTTOM_Z,p.HOPPER_THROAT_ID/2+p.HOPPER_WALL)

def shoulder(clearance=0):
    shape=z_cylinder(0,0,0,p.HOPPER_FLANGE_LAND_T,p.HOPPER_FLANGE_R+clearance)
    shape+=Pos(0,0,p.HOPPER_FLANGE_LAND_T)*Cone(
        p.HOPPER_FLANGE_R+clearance,p.HOPPER_FLANGE_TOP_R+clearance,
        p.HOPPER_FLANGE_TOP_Z-p.HOPPER_FLANGE_LAND_T,
        align=(Align.CENTER,Align.CENTER,Align.MIN))
    return shape

def funnel():
    shape=outer_funnel()
    # A broad flat underside at Z0 seats on the deck. In the rim-down print
    # pose the sloped upper shoulder grows outward gradually, without support.
    shape+=shoulder()
    inside_bottom=Circle(p.HOPPER_THROAT_ID/2)
    inside_top=Pos(0,0,p.HOPPER_TOP_Z)*Rectangle(p.HOPPER_TOP_W-2*p.HOPPER_WALL,p.HOPPER_TOP_L-2*p.HOPPER_WALL)
    shape-=loft([inside_bottom,inside_top])
    return shape-z_cylinder(0,0,p.HOPPER_BOTTOM_Z,-p.HOPPER_BOTTOM_Z,p.HOPPER_THROAT_ID/2)

def clamp(side):
    shape=bounded_box(-p.HOPPER_CLAMP_W/2,p.HOPPER_CLAMP_W/2,
                      -p.HOPPER_CLAMP_L/2,p.HOPPER_CLAMP_L/2,0,p.HOPPER_MOUNT_Z)
    for gx,gy in p.HOPPER_MOUNTS:
        x,y=gx-p.HOPPER_CENTER[0],gy-p.HOPPER_CENTER[1]
        shape+=z_cylinder(x,y,0,p.HOPPER_MOUNT_Z,p.HOPPER_MOUNT_R)
        if y < -p.HOPPER_CLAMP_L/2:
            shape+=bounded_box(x-p.HOPPER_MOUNT_R,x+p.HOPPER_MOUNT_R,y,-p.HOPPER_CLAMP_L/2,0,p.HOPPER_MOUNT_Z)
        shape-=z_cylinder(x,y,0,p.HOPPER_MOUNT_Z,p.M4_BORE/2)
        shape-=top_countersink(x,y,p.HOPPER_MOUNT_Z,p.CSK_HEAD_MAX_H,p.M4_BORE,p.CSK_RECESS_D)
    shape-=bounded_box(-p.HOPPER_CLAMP_NECK_W/2,p.HOPPER_CLAMP_NECK_W/2,
                       -p.HOPPER_CLAMP_NECK_L/2,p.HOPPER_CLAMP_NECK_L/2,0,p.HOPPER_MOUNT_Z)
    shape-=shoulder(p.HOPPER_CLAMP_CLEAR)
    xmin,xmax=(-p.HOPPER_CLAMP_W,p.HOPPER_CLAMP_GAP/-2) if side=='left' else (p.HOPPER_CLAMP_GAP/2,p.HOPPER_CLAMP_W)
    pieces=shape.intersect(bounded_box(xmin,xmax,-p.HOPPER_TOP_Z,p.HOPPER_TOP_Z,0,p.HOPPER_MOUNT_Z))
    solids=list(pieces.solids()) if hasattr(pieces,'solids') else [s for part in pieces for s in part.solids()]
    if len(solids)!=1:
        raise ValueError(f'Hopper clamp must remain one solid, got {len(solids)}')
    return solids[0]

def print_shape(role):
    shape=funnel() if role=='funnel' else clamp(role)
    shape=shape.rotate(Axis.X,180)
    b=shape.bounding_box()
    return Pos(-b.min.X,-b.min.Y,-b.min.Z)*shape
