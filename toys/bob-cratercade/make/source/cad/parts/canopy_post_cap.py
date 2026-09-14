"""Cross-bolted top shoe; vertical roof bolts join it to the roof cell."""
from build123d import Pos,Rot
import params as p
from features.primitives import bounded_box,x_cylinder,z_cylinder
from parts.canopy_nut_trap import build as nut_trap


def build():
    z0,z1=p.CANOPY_POST_TOP_Z,p.CANOPY_POST_CAP_TOP
    shape=bounded_box(*p.CANOPY_POST_CAP_OUTER_X,-p.CANOPY_POST_CAP_HALF_Y,
                      p.CANOPY_POST_CAP_HALF_Y,z0,z1)
    shape+=bounded_box(*p.CANOPY_POST_CAP_PEG_X,*p.CANOPY_POST_CAP_PEG_Y,
                       p.CANOPY_POST_CAP_PEG_BOTTOM,z0)
    for y in (-p.CANOPY_CORNER_OFFSET,p.CANOPY_CORNER_OFFSET):
        shape+=nut_trap(p.CANOPY_CORNER_OFFSET,y,post_clearance=True)
        shape-=z_cylinder(p.CANOPY_CORNER_OFFSET,y,p.CANOPY_TRAP_BOTTOM,z1-p.CANOPY_TRAP_BOTTOM,p.M4_BORE/2)
    shape-=x_cylinder(p.CANOPY_POST_CAP_PEG_X[0],
                      p.CANOPY_POST_CAP_PEG_X[1]-p.CANOPY_POST_CAP_PEG_X[0],
                      p.M4_BORE/2,0,p.CANOPY_POST_CROSS_BOLT_Z)
    return shape


def print_shape():
    return Pos(0,0,p.CANOPY_POST_CAP_TOP)*Rot(180,0,0)*build()
