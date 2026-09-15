"""Open pickup basin receiving the guarded drain and covered return route."""
from math import sqrt, sin, cos, radians
from build123d import Pos,RegularPolygon,extrude
import params as p
from features.primitives import bounded_box,z_cylinder
from features.rounded_route import footprint
from parts.return_channel import route

# Local forward extension; all shared rear, drain and mount datums stay exact.
CUP_FRONT_Y = p.CUP_Y[0]-5.0
CUP_INNER_FRONT_Y = CUP_FRONT_Y+p.CUP_WALL
# The east wall moves 4mm outward to clear the qualified drain-return lane.
# Keep p.CUP_X unchanged because its shared datums are consumed elsewhere.
CUP_OUTER_X = (p.CUP_X[0],186.0)
CUP_INNER_EAST_X = CUP_OUTER_X[1]-p.CUP_WALL
EAST_GUARD_NUT_RELIEF = (184.70,186.50,43.65,48.35,-8.45,-5.50)


def pickup_centres(diameter):
    """Lower hemisphere centres of actual Ø18×35 fingers, 20° above equator."""
    r=diameter/2
    return [(160+sign*(r+9)*cos(radians(20)), CUP_INNER_FRONT_Y+r,
             p.CUP_FLOOR_Z+r+(r+9)*sin(radians(20))) for sign in (-1,1)]


def pickup_relief():
    """Full-thickness corner openings avoid R8's feather-thin curved skins.

    Fixed3mm lower lip and18mm central front wall retain the marble. Broad
    corner access also permits the qualified single-finger recentering gesture.
    Floor-down print orientation is unchanged; no partial-depth wall remnants.
    """
    return [bounded_box(137,151,CUP_FRONT_Y-1,-11.75,-31,p.CUP_TOP_Z),
            bounded_box(169,187,CUP_FRONT_Y-1,-11.75,-31,p.CUP_TOP_Z)]


def build():
    bottom=p.CUP_FLOOR_Z-p.CUP_WALL
    shape=bounded_box(*CUP_OUTER_X,CUP_FRONT_Y,p.CUP_Y[1],bottom,p.CUP_TOP_Z)
    shape-=bounded_box(CUP_OUTER_X[0]+p.CUP_WALL,CUP_INNER_EAST_X,
                       CUP_INNER_FRONT_Y,p.CUP_Y[1]-p.CUP_WALL,
                       p.CUP_FLOOR_Z,p.CUP_TOP_Z)
    # The return enters through the northwest side, with0.25 lateral clearance.
    # Its floor ends4mm above the basin; neither mouth screws nor seams enter
    # the22mm-wide rolling corridor.
    path=route(3)
    opening=footprint(path,p.RETURN_INNER_W/2+p.RETURN_WALL+p.RAMP_SEAT_CLEARANCE,
                      True,True,p.RETURN_END_GAP,p.RETURN_GEOMETRY_BOUND)
    x,y=p.RETURN_PATHS[3][0]
    roof=p.RETURN_FLOOR_Z+p.RETURN_CLEAR_H+p.RETURN_ROOF_T+p.RAMP_SEAT_CLEARANCE
    shape-=Pos(x,y,p.CUP_FLOOR_Z)*extrude(opening,amount=roof-p.CUP_FLOOR_Z,dir=(0,0,1))
    shape-=bounded_box(*p.CUP_STRAP_NOTCH_X,*p.CUP_STRAP_NOTCH_Y,*p.CUP_STRAP_NOTCH_Z)
    for x,y in p.CUP_MOUNTS:
        shape+=z_cylinder(x,y,bottom,p.CUP_MOUNT_TOP_Z-bottom,p.CUP_MOUNT_R)
        shape-=z_cylinder(x,y,bottom,p.CUP_MOUNT_TOP_Z-bottom,p.M4_BORE/2)
        pocket_top=-2*p.DECK_T
        hexwell=extrude(RegularPolygon(p.NUT_POCKET_AF/sqrt(3),6),amount=pocket_top-bottom,dir=(0,0,1))
        shape-=Pos(x,y,bottom)*hexwell
    for cutter in pickup_relief():
        shape-=cutter
    # Open-top exterior notch clears the exact east flipper-guard jam nut.
    shape-=bounded_box(*EAST_GUARD_NUT_RELIEF)
    assert len(shape.solids())==1, "Cup reliefs must retain one cup solid"
    return shape

def print_shape():
    shape=build()
    b=shape.bounding_box()
    return Pos(-b.min.X,-b.min.Y,-b.min.Z)*shape
