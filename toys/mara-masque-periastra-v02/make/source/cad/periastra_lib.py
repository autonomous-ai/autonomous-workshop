"""Periastra Syzygy design library. Corrected revision of the published Periastra.

Base dimensions are unchanged from the published set and reproduce its exact
STEP bytes. Only the roof and the counters are new: the roof becomes a domed
observatory with a shutter slit, and the counters become Sun and Moon draughts
discs whose king step is the dome's rotation ring at counter scale.
All numerical design dimensions in mm.
"""
from build123d import *
import cadfits

# ---------------------------------------------------------------- unchanged base
BASE = 190.0
HEIGHT = 24.0
WALL = 3.0
OPENING = BASE - 2 * WALL
ROOF_CLEARANCE = 0.8
ROOF_SIZE = cadfits.peg_for(cadfits.peg_for(OPENING, "free"), "free") # two 0.4 per-side allowances
CORNER = 2.0
FLOOR = 11.0
CELL = 22.0
ROWS = 8
BOARD = CELL * ROWS
RECESS = 0.8
SQUARE_CORNER = 1.5 # continuous material at diagonal recess junctions
SQUARE_BEVEL = 0.3 # visual repair: sloped lower perimeter, unchanged mouth/pitch/depth
LEDGE_TOP = 21.0
LEDGE_DEPTH = 3.0
LEDGE_LENGTH = 24.0
SILL_TOP = 17.0 # native reveal repair: tops remain above sightline sills
PIER_INNER = 88.0
PLATE = 3.0
ROOF_CORNER = 1.2
STAR_RADIUS = 3.0
STAR_X = 22.0
RELIEF = 0.8
STAR_BEVEL = 0.25
LIFT = 100.0

# ------------------------------------------------------------------- new roof
DRUM_RADIUS = 90.0            # 180 mm across
DRUM_HEIGHT = 14.0            # z24 -> z38 closed
RING_WIDTH = 2.0              # rotation-ring seam, along the drum axis
RING_DEPTH = 1.0              # radial
RING_BELOW_TOP = 4.0          # seam centre below the top of the drum
RING_RELIEF = 1.2             # upper wall at 50 deg from vertical; 45 deg tessellates under the gate
DOME_BASE_RADIUS = 90.0
DOME_RISE = 40.0              # apex at z78 closed; deliberately not a half sphere
DOME_SPHERE_RADIUS = (DOME_BASE_RADIUS ** 2 + DOME_RISE ** 2) / (2 * DOME_RISE) # 121.25
SLIT_WIDTH = 30.0             # shutter slit, single meridian in the YZ plane
SLIT_FAR_RUN = 30.0           # how far the slit runs down the far side, along the dome surface
SLIT_FAR_Y = DOME_SPHERE_RADIUS * __import__('math').sin(SLIT_FAR_RUN / DOME_SPHERE_RADIUS)
TUBE_RADIUS = 12.0            # 24 mm across, blunt ended
TUBE_ANGLE = 45.0             # axis tilt in the YZ plane
TUBE_BACK = (0.0, -42.0, 12.0) # axis line z = -30 - y in the YZ plane
TUBE_LENGTH = 50.2
PIER_Y = (-52.0, -32.0)       # solid pier standing on the plate, full slit width
PIER_TOP = 21.0               # buries the tube's back end inside the pier
ARM_THICK = 6.0               # each fork arm, fused to an inside wall of the slit
ARM_PROFILE = [(-36.0, 3.0), (-70.0, 3.0), (-70.0, 44.0), (-63.0, 55.0), (-57.0, 44.0),
               (-40.0, 10.0)]  # fork: cradles the tube, prong rises clear above it

# --------------------------------------------------------------- new counters
COUNTER_DIAMETER = 16.0
COUNTER_HEIGHT = 7.0
COUNTER_CHAMFER = 1.0
POCKET_DEPTH = 1.2            # symbol pocket, square walls, flat floor
REBATE_WIDTH = 2.0            # king-face annular rebate
REBATE_DEPTH = 1.2
PLATEAU_DIAMETER = COUNTER_DIAMETER - 2 * REBATE_WIDTH  # 12.0
SUN_EXTENT = 10.0             # overall tip-to-tip; fixed by both face margins
SUN_BALL_DIAMETER = 4.4       # 5.0 - 1.8 ray - 1.0 band, doubled; see GEOMETRY-NOTES
SUN_RAY_COUNT = 8
SUN_RAY_INNER_WIDTH = 2.0     # widest, at the end nearest the ball
SUN_RAY_TIP_WIDTH = 1.0       # blunt flat tip, nearest the rim
SUN_RAY_GAP = 1.0             # undisturbed band between ball and every ray
# The tip corners sit ON the 10 mm frame circle, so no part of the mark reaches
# past it and both face margins hold exactly.
SUN_RAY_OUTER = ((SUN_EXTENT/2)**2 - (SUN_RAY_TIP_WIDTH/2)**2) ** 0.5
SUN_RAY_LENGTH = SUN_RAY_OUTER - (SUN_BALL_DIAMETER/2 + SUN_RAY_GAP)
MOON_OUTER_DIAMETER = 8.0     # 10.0 merges with the king rebate; see GEOMETRY-NOTES
MOON_INNER_DIAMETER = 7.2
MOON_OFFSET = 3.1             # keeps the crescent 3.5 mm at its widest point
MOON_CUT_X = 0.0              # square truncation through the outer circle poles

# SINGLE_* is the Sun counter (part keys single_01..single_12).
# FORKED_* is the Moon counter (part keys forked_01..forked_12).
BASE_COLOR = Color(0.72,0.78,0.81)
ROOF_COLOR = Color(0.19,0.36,0.43)
SINGLE_COLOR = Color(0.83,0.40,0.18)
FORKED_COLOR = Color(0.95,0.82,0.48)


def rounded_plate(size, height, radius):
    return extrude(RectangleRounded(size,size,radius), amount=height)


def build_base():
    body = rounded_plate(BASE,HEIGHT,CORNER)
    cavity = Pos(0,0,FLOOR) * Box(OPENING,OPENING,HEIGHT,align=(Align.CENTER,Align.CENTER,Align.MIN))
    body = body - cavity
    for angle in (0,90,180,270):
        opening = Pos(0,BASE/2-WALL/2,SILL_TOP)*Box(2*PIER_INNER,WALL+1,HEIGHT-SILL_TOP+1,align=(Align.CENTER,Align.CENTER,Align.MIN))
        body = body - Rot(Z=angle)*opening
    for r in range(ROWS):
        for c in range(ROWS):
            if (c+r)%2 == 0:
                x = -BOARD/2 + (c+0.5)*CELL
                y = -BOARD/2 + (r+0.5)*CELL
                cut = Pos(x,y,FLOOR-RECESS+SQUARE_BEVEL) * extrude(RectangleRounded(CELL,CELL,SQUARE_CORNER),amount=RECESS+1)
                ramp = loft([Pos(x,y,FLOOR-RECESS)*RectangleRounded(CELL-2*SQUARE_BEVEL,CELL-2*SQUARE_BEVEL,SQUARE_CORNER-SQUARE_BEVEL), Pos(x,y,FLOOR-RECESS+SQUARE_BEVEL)*RectangleRounded(CELL,CELL,SQUARE_CORNER)])
                cut = cut + ramp
                body = body-cut
    for sx,sy in [(-1,-1),(-1,1),(1,-1),(1,1)]:
        ledge = Pos(sx*(OPENING/2-LEDGE_DEPTH/2),sy*(OPENING/2-LEDGE_DEPTH/2),FLOOR) * Box(LEDGE_DEPTH,LEDGE_DEPTH,LEDGE_TOP-FLOOR,align=(Align.CENTER,Align.CENTER,Align.MIN))
        body = body + ledge
    for sign in (-1,1):
        disk = Pos(STAR_X,sign*BOARD/2,FLOOR)*Cylinder(STAR_RADIUS,RELIEF,align=(Align.CENTER,Align.CENTER,Align.MIN))
        half = Pos(STAR_X,sign*(BOARD/2+STAR_RADIUS/2),FLOOR)*Box(2*STAR_RADIUS,STAR_RADIUS,RELIEF,align=(Align.CENTER,Align.CENTER,Align.MIN))
        star = disk & half
        star = chamfer(star.edges().filter_by_position(Axis.Z,FLOOR+RELIEF,FLOOR+RELIEF),length=STAR_BEVEL)
        body = body + star
    body.label = 'base'
    body.color = BASE_COLOR
    assert len(body.solids()) == 1
    return body


def build_roof():
    """Backing plate, rotation drum, spherical-cap dome, shutter slit, telescope.

    One single solid, printed plate-down with the dome apex up.
    """
    drum_top = PLATE + DRUM_HEIGHT
    apex = drum_top + DOME_RISE
    centre_z = apex - DOME_SPHERE_RADIUS
    span = 2 * DOME_SPHERE_RADIUS

    body = rounded_plate(ROOF_SIZE, PLATE, ROOF_CORNER)
    body = body + Pos(0,0,PLATE)*Cylinder(DRUM_RADIUS,DRUM_HEIGHT,align=(Align.CENTER,Align.CENTER,Align.MIN))
    cap_box = Pos(0,0,drum_top)*Box(span,span,DOME_RISE+2,align=(Align.CENTER,Align.CENTER,Align.MIN))
    body = body + (Pos(0,0,centre_z)*Sphere(DOME_SPHERE_RADIUS) & cap_box)

    ring_top = drum_top - RING_BELOW_TOP + RING_WIDTH/2
    groove = Pos(0,0,ring_top)*Cylinder(DRUM_RADIUS+2,RING_WIDTH,align=(Align.CENTER,Align.CENTER,Align.MAX)) \
           - Pos(0,0,ring_top)*Cylinder(DRUM_RADIUS-RING_DEPTH,RING_WIDTH,align=(Align.CENTER,Align.CENTER,Align.MAX))
    # 45 deg upper wall. A square-cut ceiling here is a 178 mm-span unsupported
    # ring that check_overhang fails; see review/trial-a-square-ring-groove-overhang.md.
    relief = Pos(0,0,ring_top)*Cylinder(DRUM_RADIUS+2,RING_RELIEF,align=(Align.CENTER,Align.CENTER,Align.MIN)) \
           - Pos(0,0,ring_top)*Cone(DRUM_RADIUS-RING_DEPTH,DRUM_RADIUS,RING_RELIEF,align=(Align.CENTER,Align.CENTER,Align.MIN))
    body = body - (groove + relief)

    slit = Pos(0,SLIT_FAR_Y,PLATE)*Box(SLIT_WIDTH,span,span,align=(Align.CENTER,Align.MAX,Align.MIN))
    body = body - slit

    pier = Pos(0,sum(PIER_Y)/2,PLATE)*Box(SLIT_WIDTH,PIER_Y[1]-PIER_Y[0],PIER_TOP-PLATE,align=(Align.CENTER,Align.CENTER,Align.MIN))
    arm_face = Plane.YZ * Polygon(*ARM_PROFILE,align=None)
    arms = Pos(SLIT_WIDTH/2-ARM_THICK,0,0)*extrude(arm_face,amount=ARM_THICK) \
         + Pos(-SLIT_WIDTH/2,0,0)*extrude(arm_face,amount=ARM_THICK)
    tube = Pos(*TUBE_BACK)*Rot(X=TUBE_ANGLE)*Cylinder(TUBE_RADIUS,TUBE_LENGTH,align=(Align.CENTER,Align.CENTER,Align.MIN))
    body = body + pier + arms + tube

    body.label = 'roof'
    body.color = ROOF_COLOR
    assert len(body.solids()) == 1
    return body


def sun_symbol():
    """A ball with eight separate rays, each widest at its inner end."""
    mark = Circle(SUN_BALL_DIAMETER/2)
    inner = SUN_BALL_DIAMETER/2 + SUN_RAY_GAP
    outer = SUN_RAY_OUTER
    for i in range(SUN_RAY_COUNT):
        ray = Polygon((inner,-SUN_RAY_INNER_WIDTH/2),(outer,-SUN_RAY_TIP_WIDTH/2),
                      (outer,SUN_RAY_TIP_WIDTH/2),(inner,SUN_RAY_INNER_WIDTH/2),align=None)
        mark = mark + Rot(Z=i*360/SUN_RAY_COUNT)*ray
    return mark


def moon_symbol():
    """One bold crescent with both horns truncated square."""
    crescent = Circle(MOON_OUTER_DIAMETER/2) - Pos(MOON_OFFSET,0)*Circle(MOON_INNER_DIAMETER/2)
    keep = Pos(MOON_CUT_X,0)*Rectangle(2*MOON_OUTER_DIAMETER,2*MOON_OUTER_DIAMETER,align=(Align.MAX,Align.CENTER))
    return crescent & keep


def build_counter(forked=False):
    """A plain round draughts disc carrying the same symbol on both faces.

    Built in its print pose: the plain man face is on the bed at z=0 and the
    king face, with its annular rebate and raised plateau, is up.
    """
    radius = COUNTER_DIAMETER/2
    body = extrude(Circle(radius),amount=COUNTER_HEIGHT)
    body = chamfer(body.edges().filter_by(GeomType.CIRCLE),length=COUNTER_CHAMFER)
    rebate = Pos(0,0,COUNTER_HEIGHT)*extrude(Circle(radius+1)-Circle(PLATEAU_DIAMETER/2),amount=-REBATE_DEPTH)
    body = body - rebate
    mark = moon_symbol() if forked else sun_symbol()
    body = body - extrude(mark,amount=POCKET_DEPTH)
    body = body - Pos(0,0,COUNTER_HEIGHT)*extrude(mark,amount=-POCKET_DEPTH)
    body.label = 'moon_counter' if forked else 'sun_counter'
    body.color = FORKED_COLOR if forked else SINGLE_COLOR
    assert len(body.solids()) == 1
    return body
