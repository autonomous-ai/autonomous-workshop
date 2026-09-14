"""Upper side-wall finger relief; floor and rear wall are never cut.

Bob's completed bucket-reset-grip-design.md, with root's smaller-marble
reconciliation: 20 degree pinch for15.5 mm and15 degrees for16.5 mm. Both
18 mm fingertips clear the board-Z16 lower-lip plane in the tipped state.
The return-angle envelope is conservatively projected into YZ and clipped
by one fixed physical lower-lip mask. Digital checks still own acceptance.
"""
import math
from build123d import Axis, Pos
from shapely.geometry import MultiPoint
from features.primitives import bounded_box, yz_prism
import params as p

FINGER_RADIUS = 9.0
FINGER_LENGTH = 35.0
RELIEF_CLEARANCE = .5
ENVELOPE_ANGLE_STEP = .5
ENVELOPE_DIAMETERS = (15.5,15.75,16.0,16.25,16.5)
ENVELOPE_COLUMN_LENGTH = 100.0
ENVELOPE_SAGITTA_ALLOWANCE = .002
LIP_PLANE_BOARD_Z = 16.0


def seated_center(diameter):
    """Exact free sphere tangent to existing floor and rear wall, tipped pose."""
    radius = diameter/2
    slope = (p.BUCKET_FLOOR_Z[1]-p.BUCKET_FLOOR_Z[0])/(p.BUCKET_Y[1]-p.BUCKET_WALL-p.BUCKET_Y[0])
    y = p.BUCKET_Y[1]-p.BUCKET_WALL-radius
    z = p.BUCKET_FLOOR_Z[0]+slope*(y-p.BUCKET_Y[0])+radius*math.hypot(1, slope)
    angle = math.radians(p.JACKPOT_TRAVEL_DEG)
    return (p.JACKPOT_AXIS[0],
            p.JACKPOT_AXIS[1]+y*math.cos(angle)-z*math.sin(angle),
            p.JACKPOT_AXIS[2]+y*math.sin(angle)+z*math.cos(angle))


def pinch_centers(diameter):
    ratio = (diameter-p.MARBLE_MIN_D)/(p.MARBLE_MAX_D-p.MARBLE_MIN_D)
    if not 0 <= ratio <= 1:
        raise ValueError('Pinch poses cover only the declared marble diameter range')
    angle = math.radians(20-5*ratio)
    x, y, z = seated_center(diameter)
    separation = diameter/2+FINGER_RADIUS
    return [(x+sign*separation*math.cos(angle), y, z+separation*math.sin(angle))
            for sign in (-1, 1)]


def seated_local(diameter):
    """Existing seated geometry expressed in rocker coordinates."""
    radius=diameter/2
    slope=(p.BUCKET_FLOOR_Z[1]-p.BUCKET_FLOOR_Z[0])/(p.BUCKET_Y[1]-p.BUCKET_WALL-p.BUCKET_Y[0])
    y=p.BUCKET_Y[1]-p.BUCKET_WALL-radius
    z=p.BUCKET_FLOOR_Z[0]+slope*(y-p.BUCKET_Y[0])+radius*math.hypot(1,slope)
    return (0.0,y,z)


def protected_mask():
    """One fixed physical lip plane: tipped board Z>=16, inverse transformed."""
    clip=bounded_box(100,190,370,440,LIP_PLANE_BOARD_Z,100)
    return (Pos(*(-v for v in p.JACKPOT_AXIS))*clip).rotate(Axis.X,-p.JACKPOT_TRAVEL_DEG)


def envelope_profile():
    """Conservative projected capsule sweep, not a material-performance model.

    Projection drops X distance, so a YZ radius9.5 disk contains every sphere
    section through a2mm side wall. Convex hull adds conservative material
    removal between angles/diameters. Circumscribed polygon buffering plus
    .002 sagitta allowance encloses the continuous angular arc (R<110mm).
    """
    points=[]
    count=round(-p.JACKPOT_TRAVEL_DEG/ENVELOPE_ANGLE_STEP)
    for diameter in ENVELOPE_DIAMETERS:
        _,y,z=seated_local(diameter)
        up=pinch_centers(diameter)[0][2]-seated_center(diameter)[2]
        for i in range(count+1):
            a=math.radians(p.JACKPOT_TRAVEL_DEG+i*ENVELOPE_ANGLE_STEP)
            for length in (up,up+ENVELOPE_COLUMN_LENGTH):
                points.append((y+length*math.sin(a),z+length*math.cos(a)))
    q=16
    radius=(FINGER_RADIUS+RELIEF_CLEARANCE+ENVELOPE_SAGITTA_ALLOWANCE)/math.cos(math.pi/(4*q))
    polygon=MultiPoint(points).convex_hull.buffer(radius,resolution=q)
    assert polygon.geom_type=='Polygon' and not polygon.interiors
    return list(polygon.exterior.coords)[:-1]


def cutters():
    """Return one conservative cutter per side; consumers cut side walls only."""
    profile=envelope_profile(); mask=protected_mask()
    sides=[]
    for xa,xb in ((p.BUCKET_X[0]-1,p.BUCKET_X[0]+p.BUCKET_WALL+1),
                  (p.BUCKET_X[1]-p.BUCKET_WALL-1,p.BUCKET_X[1]+1)):
        # Remove the acute upper-front side-wall remnant identified by the
        # R7/R8 thickness gate. This trim only enlarges the finger opening;
        # the existing physical lower-lip mask still clips the entire cutter.
        upper_front_trim=bounded_box(xa,xb,3,8,24,60)
        cutter=(yz_prism(xa,xb,profile)+upper_front_trim).intersect(mask)
        if not hasattr(cutter,'wrapped'):
            assert len(cutter)==1
            cutter=cutter[0]
        assert len(cutter.solids())==1 and cutter.is_valid
        sides.append(cutter)
    return sides
