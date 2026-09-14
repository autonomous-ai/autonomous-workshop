"""Freestanding divider half; feet project away from the marble launch lane."""
from build123d import Pos
import params as p
from features.primitives import bounded_box,z_cylinder,top_countersink

def build(index=0):
    ends=(p.DIVIDER_Y0,p.DIVIDER_SPLIT_Y,p.DIVIDER_Y1)
    y0,y1=ends[index:index+2]
    gap=p.PERIMETER_JOINT_CLEARANCE/2
    body=bounded_box(0,p.DIVIDER_W,gap,y1-y0-gap,0,p.PLAYFIELD_WALL_H)
    for board_y in p.DIVIDER_BOLT_Y[index]:
        x,y=p.DIVIDER_BOLT_X-p.DIVIDER_X,board_y-y0
        body+=z_cylinder(x,y,0,p.PLAYFIELD_ROOT_T,p.DIVIDER_FOOT_R)
        body-=z_cylinder(x,y,-p.PLAYFIELD_CUT_MARGIN,p.PLAYFIELD_WALL_H+2*p.PLAYFIELD_CUT_MARGIN,p.M4_BORE/2)
        body-=top_countersink(x,y,p.PLAYFIELD_ROOT_T,p.PLAYFIELD_CSK_DEPTH,p.M4_BORE,p.CSK_RECESS_D)
    assert len(body.solids())==1
    return body

def print_shape(index=0):
    body=build(index)
    box=body.bounding_box()
    return Pos(-box.min.X,-box.min.Y,0)*body
