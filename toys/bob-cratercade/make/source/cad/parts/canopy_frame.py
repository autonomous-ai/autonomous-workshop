"""One roof cell's lower frame; local datum is its south-west cell corner."""
import params as p
from features.primitives import bounded_box,z_cylinder,top_countersink


def bolt_points():
    d=p.CANOPY_CORNER_OFFSET
    return ((d,d),(p.CANOPY_CELL_W-d,d),
            (d,p.CANOPY_CELL_L-d),(p.CANOPY_CELL_W-d,p.CANOPY_CELL_L-d))


def clamp_points():
    d=p.CANOPY_CLAMP_OFFSET
    return ((d,p.CANOPY_CELL_L/2),(p.CANOPY_CELL_W-d,p.CANOPY_CELL_L/2),
            (p.CANOPY_CELL_W/2,d),(p.CANOPY_CELL_W/2,p.CANOPY_CELL_L-d))


def outline(z0,z1):
    g=p.CANOPY_CELL_GAP/2; r=p.CANOPY_RIM_W
    shape=bounded_box(g,p.CANOPY_CELL_W-g,g,p.CANOPY_CELL_L-g,z0,z1)
    shape-=bounded_box(r,p.CANOPY_CELL_W-r,r,p.CANOPY_CELL_L-r,z0,z1)
    for x,y in bolt_points():
        shape+=z_cylinder(x,y,z0,z1-z0,p.CANOPY_CORNER_R)
    for x,y in clamp_points():
        shape+=z_cylinder(x,y,z0,z1-z0,p.CANOPY_CLAMP_R)
    return shape


def build():
    shape=outline(p.CANOPY_FRAME_BOTTOM,p.CANOPY_FRAME_TOP)
    for x,y in clamp_points():
        shape+=z_cylinder(x,y,p.CANOPY_FRAME_TOP,
                          p.CANOPY_CAP_BOTTOM-p.CANOPY_FRAME_TOP,p.CANOPY_CAP_STANDOFF_R)
        shape-=z_cylinder(x,y,p.CANOPY_FRAME_BOTTOM,
                          p.CANOPY_CAP_BOTTOM-p.CANOPY_FRAME_BOTTOM,p.M4_BORE/2)
    for x,y in bolt_points():
        shape-=z_cylinder(x,y,p.CANOPY_FRAME_BOTTOM,
                          p.CANOPY_FRAME_TOP-p.CANOPY_FRAME_BOTTOM,p.M4_BORE/2)
        shape-=top_countersink(x,y,p.CANOPY_FRAME_TOP,p.CSK_HEAD_MAX_H,
                              p.M4_BORE,p.CSK_RECESS_D)
    assert len(shape.solids())==1
    return shape
