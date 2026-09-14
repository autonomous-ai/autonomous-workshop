"""Two-sheet end mullion hung from corner bolts of the two adjacent roof cells."""
from build123d import Pos,Rot
import params as p
from features.primitives import bounded_box,z_cylinder
from parts.canopy_nut_trap import build as nut_trap


def build(rear=False):
    sy=p.CANOPY_END_PANEL_Y[1 if rear else 0]
    xh=p.CANOPY_END_JOIN_HALF_W; yh=p.CANOPY_END_JOIN_HALF_L
    z0,z1=p.CANOPY_END_JOIN_BOTTOM,p.CANOPY_END_JOIN_TOP+p.CANOPY_ROOF_LIFT
    frame_top=p.CANOPY_FRAME_BOTTOM+p.CANOPY_ROOF_LIFT
    shape=bounded_box(-xh,xh,sy-yh,sy+yh,z0,z1)
    slot_bottom=z0+p.CANOPY_SLOT_FLOOR; half=p.CANOPY_PET_SLOT_W/2
    a,b,c,d=p.CANOPY_END_JOIN_SLOT_X
    for xa,xb in ((a,b),(c,d)):
        shape-=bounded_box(xa,xb,sy-half,sy+half,slot_bottom,z1)
    ya,yb=p.CANOPY_END_BRACKET_Y
    if rear: ya,yb=-yb,-ya
    shape+=bounded_box(-p.CANOPY_END_BRACKET_HALF_W,p.CANOPY_END_BRACKET_HALF_W,
                       ya,yb,z1,frame_top)
    bolt_y=-p.CANOPY_CORNER_OFFSET if rear else p.CANOPY_CORNER_OFFSET
    for x in (-p.CANOPY_CORNER_OFFSET,p.CANOPY_CORNER_OFFSET):
        shape+=Pos(0,0,p.CANOPY_ROOF_LIFT)*nut_trap(x,bolt_y,outward=1 if x>0 else -1)
        shape-=z_cylinder(x,bolt_y,p.CANOPY_TRAP_BOTTOM+p.CANOPY_ROOF_LIFT,p.CANOPY_FRAME_BOTTOM-p.CANOPY_TRAP_BOTTOM,p.M4_BORE/2)
    return shape


def print_shape(rear=False):
    return Pos(0,0,p.CANOPY_FRAME_BOTTOM+p.CANOPY_ROOF_LIFT)*Rot(180,0,0)*build(rear)
