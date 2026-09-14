"""Open-bottom hood and removable smooth floor for one return-route section."""
from functools import lru_cache
from math import sqrt
from build123d import Align,Cone,Pos,RegularPolygon,extrude
import params as p
from features.primitives import z_cylinder,top_countersink
from features.rounded_route import centerline,footprint,station

@lru_cache(maxsize=4)
def route(index):
    x0,y0=p.RETURN_PATHS[index][0]
    points=[(x-x0,y-y0) for x,y in p.RETURN_PATHS[index]]
    return centerline(points,p.RETURN_BEND_R)

def mount_points(index,floor=False):
    fractions=p.RETURN_FLOOR_FRACTIONS[index] if floor else p.RETURN_ROOT_FRACTIONS[index]
    sign=-1 if floor else 1
    return [station(route(index),f,sign*(1 if i==0 else -1)*p.RETURN_MOUNT_OFFSET)
            for i,f in enumerate(fractions)]

def section_face(index,inner=False):
    radius=p.RETURN_INNER_W/2+(0 if inner else p.RETURN_WALL)
    return footprint(route(index),radius,index!=0,True,p.RETURN_END_GAP,p.RETURN_GEOMETRY_BOUND)

def hood(index,ceiling_holes=()):
    outer,inner=section_face(index),section_face(index,True)
    ceiling=p.RETURN_CLEAR_H
    shape=extrude(outer,amount=ceiling+p.RETURN_ROOF_T,dir=(0,0,1))
    if index==0:
        shape+=z_cylinder(0,0,0,ceiling+p.RETURN_ROOF_T,p.RETURN_PORT_RIM_R)
    shape-=extrude(inner,amount=ceiling,dir=(0,0,1))
    if index==0:
        shape-=z_cylinder(0,0,0,ceiling+p.RETURN_ROOF_T,(p.HOPPER_THROAT_ID+2*p.HOPPER_WALL+.5)/2)
    for x,y in mount_points(index):
        # Top at board underside. The through-deck screw seats a nut beneath
        # this four-millimetre boss, outside the marble corridor.
        top=-p.DECK_T-p.RETURN_FLOOR_Z
        shape+=z_cylinder(x,y,ceiling,top-ceiling,p.RETURN_MOUNT_R)
        shape-=z_cylinder(x,y,ceiling,top-ceiling,p.M4_BORE/2)
    for x,y in mount_points(index,True):
        top=-p.DECK_T-p.RETURN_FLOOR_Z
        shape+=z_cylinder(x,y,0,top,p.RETURN_MOUNT_R)
        shape-=z_cylinder(x,y,0,top,p.M4_BORE/2)
        # Nut loads from the open top before the hood meets the deck. Its
        # hexagonal well seats it at8 and leaves every printed column rooted.
        pocket=extrude(RegularPolygon(p.NUT_POCKET_AF/sqrt(3),6),
                       amount=top-p.RETURN_FLOOR_TAB_H,dir=(0,0,1))
        shape-=Pos(x,y,p.RETURN_FLOOR_TAB_H)*pocket
    x0,y0=p.RETURN_PATHS[index][0]
    top=-p.DECK_T-p.RETURN_FLOOR_Z
    box=shape.bounding_box()
    for gx,gy in ceiling_holes:
        x,y=gx-x0,gy-y0
        # Only the outlet pocket at this apron root opens through the rim.
        # Other outlet pockets retain their thicker flat bridge ceilings.
        conical = index==0 or (index==3 and (gx,gy)==p.APRON_MOUNTS['right'][0])
        radius=p.RETURN_ROOF_RELIEF_R if conical else p.RETURN_ROOF_NUT_CLEAR_R
        if not(box.min.X-radius<=x<=box.max.X+radius and box.min.Y-radius<=y<=box.max.Y+radius):
            continue
        if conical:
            depth=radius/p.RETURN_ROOF_RELIEF_SLOPE
            # The inlet and diagonal outlet have side-opening nut pockets.
            # Their ceilings close at43.5deg in the roof-down print pose;
            # this also supports the outlet's apron-nut relief at its edge.
            shape-=Pos(x,y,top-depth)*Cone(0,radius,depth,
                       align=(Align.CENTER,Align.CENTER,Align.MIN))
        else:
            shape-=z_cylinder(x,y,top-p.NUT_T-p.RETURN_ROOF_NUT_CLEAR,
                              p.NUT_T+p.RETURN_ROOF_NUT_CLEAR,radius)
            shape-=z_cylinder(x,y,ceiling,p.RETURN_ROOF_T,p.M4_BORE/2)
    return shape

def floor_lid(index):
    shape=Pos(0,0,-p.RETURN_LID_T)*extrude(section_face(index),amount=p.RETURN_LID_T,dir=(0,0,1))
    if index==0:
        shape+=z_cylinder(0,0,-p.RETURN_LID_T,p.RETURN_LID_T,p.RETURN_PORT_RIM_R)
    for i,(x,y) in enumerate(mount_points(index,True)):
        shape+=z_cylinder(x,y,-p.RETURN_LID_T,p.RETURN_LID_T,p.RETURN_MOUNT_R)
        shape-=z_cylinder(x,y,-p.RETURN_LID_T,p.RETURN_LID_T,p.M4_BORE/2)
        # Counterbore on the underside: rotate the same qualified conical cut.
        from build123d import Axis
        shape-=Pos(x,y,-p.RETURN_LID_T)*top_countersink(0,0,0,p.CSK_HEAD_MAX_H,p.M4_BORE,p.CSK_RECESS_D).rotate(Axis.X,180)
    return shape

def print_shape(index,floor=False,ceiling_holes=()):
    from build123d import Axis
    shape=(floor_lid(index) if floor else hood(index,ceiling_holes)).rotate(Axis.X,180)
    b=shape.bounding_box()
    return Pos(-b.min.X,-b.min.Y,-b.min.Z)*shape
