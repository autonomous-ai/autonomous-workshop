"""Periastra text-derived design. Dimensions from completed Mara handoff.
All numerical design dimensions [assumed] from WISH/design.md, in mm.
"""
from build123d import *
import cadfits

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
CONE_RADIUS = 90.0
CONE_TOP = 8.0
CONE_HEIGHT = 45.0
STAR_RADIUS = 3.0
STAR_X = 22.0
RELIEF = 0.8
STAR_BEVEL = 0.25
HOOD_RADIUS = 9.0
HOOD_LENGTH = 38.0
HOOD_ANGLE = 45.0
HOOD_START = (0, -28, 23)
HOOD_SUPPORT = [(-28,3),(-61,3),(-61,43),(-28,23)]
APERTURE_RADIUS = 6.0
APERTURE_DEPTH = 0.6
COUNTER_HEIGHT = 7.0
HEAD_RADIUS = 6.0
HEAD_Y = 2.0
SINGLE_TAIL = [(-4,0),(-1.5,-8),(1.5,-8),(4,0)]
FORKED_TAIL = [(-4.5,0),(-4.5,-8),(-1.5,-8),(-1.5,-3),(1.5,-3),(1.5,-8),(4.5,-8),(4.5,0)]
TAIL_ROUND = 0.6
CROWN_OUTER = (4.5,3.0)
CROWN_INNER = (2.7,1.3)
CROWN_DEPTH = 0.6
CROWN_NOTCH_X = (-2.8,0,2.8)
CROWN_NOTCH_Y = 4.4
CROWN_NOTCH_WIDTH = 1.6
CROWN_NOTCH_HEIGHT = 1.8
LIFT = 100.0
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
    body = rounded_plate(ROOF_SIZE,PLATE,ROOF_CORNER)
    body = body + Pos(0,0,PLATE)*Cone(CONE_RADIUS,CONE_TOP,CONE_HEIGHT,align=(Align.CENTER,Align.CENTER,Align.MIN))
    hood_pose = Pos(*HOOD_START)*Rot(X=HOOD_ANGLE)
    hood = hood_pose*Cylinder(HOOD_RADIUS,HOOD_LENGTH,align=(Align.CENTER,Align.CENTER,Align.MIN))
    aperture = hood_pose*Pos(0,0,HOOD_LENGTH-APERTURE_DEPTH)*Cylinder(APERTURE_RADIUS,APERTURE_DEPTH+1,align=(Align.CENTER,Align.CENTER,Align.MIN))
    support_face = Plane.YZ * Polygon(*HOOD_SUPPORT,align=None)
    support = extrude(support_face,amount=HOOD_RADIUS,both=True)
    body = (body+support+hood)-aperture
    body.label = 'roof'
    body.color = ROOF_COLOR
    assert len(body.solids()) == 1
    return body


def build_counter(forked=False):
    outline = Pos(0,HEAD_Y)*Circle(HEAD_RADIUS) + Polygon(*(FORKED_TAIL if forked else SINGLE_TAIL),align=None)
    body = extrude(outline,amount=COUNTER_HEIGHT)
    body = fillet(body.edges().filter_by(Axis.Z),radius=TAIL_ROUND)
    ring = Pos(0,HEAD_Y)*(Ellipse(*CROWN_OUTER)-Ellipse(*CROWN_INNER))
    for x in CROWN_NOTCH_X:
        ring = ring + Pos(x,CROWN_NOTCH_Y)*Rectangle(CROWN_NOTCH_WIDTH,CROWN_NOTCH_HEIGHT)
    crown = Pos(0,0,COUNTER_HEIGHT-CROWN_DEPTH)*extrude(ring,amount=CROWN_DEPTH+1)
    body = body-crown
    body.label = 'forked_comet' if forked else 'single_comet'
    body.color = FORKED_COLOR if forked else SINGLE_COLOR
    assert len(body.solids()) == 1
    return body
