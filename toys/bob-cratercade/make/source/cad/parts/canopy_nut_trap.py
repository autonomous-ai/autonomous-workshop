"""Side-loaded thin-nut cage for a vertical removable roof mounting screw."""
from build123d import Plane,Pos
import params as p
from features.primitives import bounded_box,z_cylinder


def build(x,y,outward=1,post_clearance=False):
    lo,hi=p.CANOPY_TRAP_X; half=p.CANOPY_TRAP_HALF_Y; wall=p.CANOPY_TRAP_WALL
    z0=p.CANOPY_TRAP_BOTTOM; z1=p.CANOPY_POST_TOP_Z
    body=bounded_box(lo,hi,-half-wall,half+wall,z0,z1)
    body-=bounded_box(p.CANOPY_TRAP_INNER_X,hi,-half,half,z0+p.CANOPY_TRAP_FLOOR,z1)
    body-=z_cylinder(0,0,z0,z1-z0,p.M4_BORE/2)
    if outward<0: body=body.mirror(Plane.YZ)
    body=Pos(x,y,0)*body
    if post_clearance:
        c=p.CANOPY_CELL_GAP+p.CANOPY_CELL_GAP/2
        body-=bounded_box(p.CANOPY_POST_OUTER_X[0]-c,p.CANOPY_POST_OUTER_X[1]+c,
                          p.CANOPY_POST_OUTER_Y[0]-c,p.CANOPY_POST_OUTER_Y[1]+c,z0,z1)
        body-=bounded_box(p.CANOPY_TRAP_X[0]+x,p.CANOPY_TRAP_X[1]+x,
                          -p.CANOPY_TRAP_POST_INNER_Y,p.CANOPY_TRAP_POST_INNER_Y,z0,z1)
    return body
