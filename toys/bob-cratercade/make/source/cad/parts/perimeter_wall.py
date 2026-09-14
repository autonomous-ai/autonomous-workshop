"""Bolted perimeter segment, local interior +X and length +Y.

The 13 mm root towers keep an accessible Z6 countersink below each wall well.
Their 1.5 mm outboard projection avoids narrowing the launch lane below22.5.
"""
from build123d import Plane,Pos
import params as p
from features.primitives import bounded_box,z_cylinder,top_countersink
from parts.canopy_post import root_cutter

def build(length=None, bolt_y=None, mirror=False, post_y=()):
    length=p.PERIMETER_LENGTHS[0] if length is None else length
    bolt_y=p.PERIMETER_SIDE_BOLTS[0] if bolt_y is None else bolt_y
    gap=p.PERIMETER_JOINT_CLEARANCE/2
    body=bounded_box(0,p.PERIMETER_BASE_W,gap,length-gap,0,p.PLAYFIELD_ROOT_T)
    body+=bounded_box(p.PERIMETER_BASE_W-p.PLAYFIELD_WALL_T,p.PERIMETER_BASE_W,
                      gap,length-gap,0,p.PLAYFIELD_WALL_H)
    for y in bolt_y:
        x=p.PERIMETER_BOLT_X
        body+=z_cylinder(x,y,0,p.PLAYFIELD_WALL_H,p.PLAYFIELD_ROOT_R)
        body-=z_cylinder(x,y,-p.PLAYFIELD_CUT_MARGIN,p.PLAYFIELD_WALL_H+2*p.PLAYFIELD_CUT_MARGIN,p.M4_BORE/2)
        body-=z_cylinder(x,y,p.PLAYFIELD_ROOT_T,p.PLAYFIELD_WALL_H,p.PLAYFIELD_ACCESS_D/2)
        body-=top_countersink(x,y,p.PLAYFIELD_ROOT_T,p.PLAYFIELD_CSK_DEPTH,p.M4_BORE,p.CSK_RECESS_D)
    for y in post_y:
        body+=z_cylinder(p.CANOPY_POST_ROOT_X,y,0,p.PLAYFIELD_WALL_H,p.PLAYFIELD_ROOT_R)
        body-=root_cutter(y)
    if mirror:
        body=body.mirror(Plane.YZ)
    assert len(body.solids())==1
    return body

def print_shape(length=None,bolt_y=None,mirror=False,post_y=()):
    body=build(length,bolt_y,mirror,post_y)
    box=body.bounding_box()
    return Pos(-box.min.X,-box.min.Y,0)*body
