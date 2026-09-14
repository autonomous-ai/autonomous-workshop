"""Bolted roof clamp; captures the PET between two flat frame surfaces."""
import params as p
from parts.canopy_frame import outline,bolt_points,clamp_points
from features.primitives import z_cylinder,top_countersink


def build():
    z0=p.CANOPY_CAP_BOTTOM; top=z0+p.CANOPY_CAP_T
    shape=outline(z0,top)
    for x,y in clamp_points():
        shape-=z_cylinder(x,y,z0,p.CANOPY_CAP_T,p.M4_BORE/2)
        shape-=top_countersink(x,y,top,p.CSK_HEAD_MAX_H,p.M4_BORE,p.CSK_RECESS_D)
    for x,y in bolt_points():
        shape-=z_cylinder(x,y,z0,p.CANOPY_CAP_T,p.CANOPY_CORNER_ACCESS_D/2)
    assert len(shape.solids())==1
    return shape
