"""Common sample bucket and flag, local origin at the transverse axle.

Original Bob design; entry raised 10 mm after exact axle-path reconciliation.
All features are one rigid solid. Mass properties and printability are checked
on the built result, not inferred from this construction.
"""
from build123d import Plane,Polygon,Pos,extrude
import params as p
from features.primitives import bounded_box, x_cylinder, yz_prism
from parts.bucket_grip_relief import cutters as finger_relief_cutters

def make_bucket_floor():
    y0, y1 = p.BUCKET_Y
    z0, z1 = p.BUCKET_FLOOR_Z
    w = p.BUCKET_WALL
    return yz_prism(*p.BUCKET_X, [(y0,z0),(y1-w,z1),(y1,z1),
                                  (y1,p.ROCKER_PRINT_BASE_Z),(y0,p.ROCKER_PRINT_BASE_Z)])

def make_bucket_walls():
    x0,x1 = p.BUCKET_X
    y0,y1 = p.BUCKET_Y
    z0,z1 = p.BUCKET_FLOOR_Z
    h0,h1 = p.BUCKET_RIM_Z
    w = p.BUCKET_WALL
    side = [(y0,z0-w),(y1-w,z1-w),(y1,z1-w),(y1,h1),(y0,h0)]
    left, right = finger_relief_cutters()
    # Restrict relief to the two side-wall solids. Floor/rear capture wall,
    # lower hub, flag and trim remain exact independent constructions.
    return ((yz_prism(x0,x0+w,side)-left) + (yz_prism(x1-w,x1,side)-right)
            + bounded_box(x0,x1,y1-w,y1,z1-w,h1))

def make_axis_and_root_webs():
    body = x_cylinder(p.ROCKER_HUB_X0,p.ROCKER_HUB_W,p.ROCKER_HUB_R)
    body += bounded_box(p.ROCKER_HUB_X0,p.ROCKER_HUB_X0+p.ROCKER_HUB_W,
                        -p.ROCKER_HUB_BASE_HALF_W,p.ROCKER_HUB_BASE_HALF_W,
                        p.ROCKER_PRINT_BASE_Z,p.ROCKER_HUB_BASE_TOP)
    for x0 in (p.BUCKET_X[0],p.BUCKET_X[1]-p.BUCKET_WALL):
        body += bounded_box(x0,x0+p.BUCKET_WALL,p.BUCKET_Y[0],p.ROCKER_WEB_Y1,
                            p.ROCKER_WEB_BOTTOM,p.BUCKET_FLOOR_Z[0])
    return body

def make_common_flag():
    x, y = p.FLAG_ARM_X, p.FLAG_ARM_Y
    w,t = p.FLAG_ARM_W,p.FLAG_ARM_T
    base=p.ROCKER_PRINT_BASE_Z
    arm = bounded_box(x-w/2,x+w/2,y,0,base,base+t)
    pole = bounded_box(x-p.FLAG_POLE_W/2,x+p.FLAG_POLE_W/2,
                       y-p.FLAG_POLE_T/2,y+p.FLAG_POLE_T/2,base,p.FLAG_TOP_Z)
    panel = bounded_box(x-p.FLAG_PANEL_W/2,x+p.FLAG_PANEL_W/2,
                        y-p.FLAG_PANEL_T/2,y+p.FLAG_PANEL_T/2,
                        p.FLAG_TOP_Z-p.FLAG_PANEL_H,p.FLAG_TOP_Z)
    # Sloping lower shoulders support the broad flag during flat-base printing.
    panel_bottom=p.FLAG_TOP_Z-p.FLAG_PANEL_H
    shoulder=Plane.XZ*Polygon(
        (x-p.FLAG_POLE_W/2,panel_bottom-p.FLAG_PANEL_GUSSET_H),
        (x+p.FLAG_POLE_W/2,panel_bottom-p.FLAG_PANEL_GUSSET_H),
        (x+p.FLAG_PANEL_W/2,panel_bottom),
        (x-p.FLAG_PANEL_W/2,panel_bottom),align=None)
    gusset=Pos(0,y-p.FLAG_PANEL_T/2,0)*extrude(shoulder,amount=p.FLAG_PANEL_T,dir=(0,1,0))
    return arm+pole+panel+gusset

def build_rocker():
    rocker = make_bucket_floor()+make_bucket_walls()+make_axis_and_root_webs()+make_common_flag()
    bore = x_cylinder(p.ROCKER_HUB_X0-p.BUCKET_WALL,
                      p.ROCKER_HUB_W+2*p.BUCKET_WALL,p.AXLE_BORE/2)
    # Slot ends are squared at this proof step; rounding is a later local feature.
    slot = bounded_box(p.FLAG_ARM_X-p.TRIM_SLOT_W/2,p.FLAG_ARM_X+p.TRIM_SLOT_W/2,
                       *p.TRIM_SLOT_Y,p.ROCKER_PRINT_BASE_Z-p.FLAG_ARM_T,
                       p.ROCKER_PRINT_BASE_Z+2*p.FLAG_ARM_T)
    return rocker-bore-slot
