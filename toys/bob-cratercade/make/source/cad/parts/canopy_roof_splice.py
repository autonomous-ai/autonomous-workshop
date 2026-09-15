"""Four-bolt crossing plate above the playfield, with no central upright."""
import params as p
from features.primitives import bounded_box,z_cylinder
from parts.canopy_nut_trap import build as nut_trap


def build():
    z0=p.CANOPY_POST_TOP_Z; z1=p.CANOPY_FRAME_BOTTOM
    shape=bounded_box(-p.CANOPY_SPLICE_W/2,p.CANOPY_SPLICE_W/2,
                      -p.CANOPY_SPLICE_L/2,p.CANOPY_SPLICE_L/2,z0,z1)
    for x in (-p.CANOPY_CORNER_OFFSET,p.CANOPY_CORNER_OFFSET):
        for y in (-p.CANOPY_CORNER_OFFSET,p.CANOPY_CORNER_OFFSET):
            shape+=nut_trap(x,y,outward=1 if x>0 else -1)
            shape-=z_cylinder(x,y,p.CANOPY_TRAP_BOTTOM,z1-p.CANOPY_TRAP_BOTTOM,p.M4_BORE/2)
    # The 401-sample reset also reaches the outer cage mouth at local
    # X20..21,Y-7.583..-7.3,Z96.4..96.63. Remove its complete wall tip,
    # avoiding a thin remnant, while preserving the nut-bearing region
    # inboard of X19 and 2.8 mm of the four-mm roof plate.
    shape-=bounded_box(*p.CANOPY_SPLICE_FLAG_RELIEF_X,*p.CANOPY_SPLICE_FLAG_RELIEF_Y,
                       p.CANOPY_TRAP_BOTTOM,z0+p.CANOPY_SPLICE_FLAG_RELIEF_H)
    return shape
