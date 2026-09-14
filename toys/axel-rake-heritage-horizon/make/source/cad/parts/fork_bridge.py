from build123d import *
from math import sqrt
from params import *
from features.common import box_bounds, prism_xz

def build():
    s=box_bounds(FRAME_BRIDGE_MAIN)
    s=s.fuse(box_bounds(FRAME_BRIDGE_TONGUE),box_bounds(FRAME_RISER_LAND))
    lamp=Pos(*FRAME_LAMP_ORIGIN)*Rot(0,90,0)*Cylinder(FRAME_LAMP_R,FRAME_LAMP_DEPTH,align=(Align.CENTER,Align.CENTER,Align.MIN))
    lamp=lamp.intersect(box_bounds(FRAME_LAMP_HALF_CLIP))[0]
    s=s.fuse(lamp)
    length=sqrt(COCKPIT_SCREEN_RISE**2+COCKPIT_SCREEN_SWEEP**2)
    plane=Plane(origin=COCKPIT_SCREEN_ORIGIN,x_dir=(0,1,0),z_dir=(COCKPIT_SCREEN_RISE/length,0,COCKPIT_SCREEN_SWEEP/length))
    # Same insertion frame as screen; roof opens to upper edge and center seam.
    pocket=plane*Pos(0,-COCKPIT_TONGUE_LENGTH/2)*Rectangle(FRAME_SCREEN_SOCKET_W,FRAME_SCREEN_SOCKET_L)
    cutter=Pos(-FRAME_SCREEN_CLEAR*COCKPIT_SCREEN_RISE/length,0,-FRAME_SCREEN_CLEAR*COCKPIT_SCREEN_SWEEP/length)*extrude(pocket,amount=FRAME_SCREEN_SOCKET_T)
    return s.cut(cutter)
