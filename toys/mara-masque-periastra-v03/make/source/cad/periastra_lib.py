"""Periastra Meridian design library, revision C: centred yoke, inlaid board.

This revision corrects exactly two things and changes nothing else.

A. The yoke arms were both 4.000 mm off centre because `extrude()` grew the arm
   face along its own normal, which follows the polygon winding order, so the
   two hand-written offsets landed the arms at [-13,-9] and [+1,+5] instead of
   [-9,-5] and [+5,+9]. They are now built once and MIRRORED, a construction
   that cannot depend on winding order. See `build_roof`.

B. The board's 32 dark cells were a 0.8 mm recess with a 0.3 mm lip, which is
   not a chequerboard a seated player can read. They are now the house
   tiled-board FIT LAYER: blind 22.0 mm pockets 2.0 mm deep with 1.0 mm plan
   corner chamfers, each holding a separate 21.5 x 2.0 mm inlay printed in a
   contrasting colour and finishing flush with the board floor. RECESS,
   SQUARE_BEVEL and SQUARE_CORNER are gone; they were the mechanism this
   replaces.

The two counters are FROZEN. `measure/check_fit.py` asserts their exact
published sha256 on every run and fails the build if either moves.
All numerical design dimensions in mm.
"""
import math

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

# ------------------------------------------- board fit layer (tiled-board baseline)
# Scaled to this product's 22.0 mm square from references/tiled-board-baseline.md.
# Clauses relied on and every deliberate override are cited in GEOMETRY-NOTES.md.
POCKET_SIZE = CELL            # baseline "pocket opening = the playing square": carried
INLAY_SIZE = 21.5             # baseline 0.5 mm total straight-edge clearance: carried UNSCALED
POCKET_DEPTH = 2.0            # override of the baseline 2.6; this floor is 11.0, so depth is free
INLAY_THICK = POCKET_DEPTH    # baseline: the inlay finishes FLUSH
BACKING = FLOOR - POCKET_DEPTH        # 9.0 continuous backing; baseline minimum 2.4, pocket BLIND
INLAY_CHAMFER = 1.0           # baseline 2.0 at a 42 mm square, scaled: 2.0 * 22/42 = 1.048
INLAY_CLEARANCE = (POCKET_SIZE - INLAY_SIZE)/2        # 0.25 per side when centred
BRIDGE = 2*INLAY_CHAMFER/math.sqrt(2)                 # 1.414 material bridge at a diagonal junction
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

# -------------------------------------------------- roof: 150 mm observatory dome
# Roof-local z0 is the flat underside of the backing plate; it seats on the base
# ledges at z21, so every closed-state height below is 21 mm higher.
DRUM_RADIUS = 75.0            # 150 mm across (was 90.0 / 180 mm)
DRUM_HEIGHT = 11.7            # 14.0 x 150/180; drum runs z24 -> z35.7 closed
RING_WIDTH = 2.0              # rotation-ring seam, along the drum axis
RING_DEPTH = 1.0              # radial
RING_BELOW_TOP = 4.0          # seam centre below the top of the drum
RING_RELIEF = 1.2             # upper wall relieved at 50 deg; the shape that passed check_overhang
DOME_SPHERE_RADIUS = 75.0     # EXACT HEMISPHERE: sphere radius == base radius
DOME_BASE_RADIUS = DOME_SPHERE_RADIUS
DOME_RISE = DOME_SPHERE_RADIUS # rise 75.0, apex at z110.7 closed
SLIT_WIDTH = 30.0             # kept at its built absolute size, never scaled with the dome
SLIT_FAR_RUN = 30.0           # surface arc down the far side: 30/75 rad = 22.9 deg past the apex
SLIT_FAR_Y = DOME_SPHERE_RADIUS * math.sin(SLIT_FAR_RUN / DOME_SPHERE_RADIUS)

# Telescope: kept exactly at the size the previous attempt proved. Only its
# placement is re-solved for the smaller dome.
TUBE_RADIUS = 7.5             # 15.0 mm outer diameter
TUBE_BORE_RADIUS = 3.5        # 7.0 mm muzzle bore -> 4.0 mm tube wall
TUBE_BORE_DEPTH = 13.0        # blind, >= 12.0
TUBE_LENGTH = 45.0
TUBE_ELEVATION = 35.0         # degrees above horizontal, in the YZ plane
TUBE_BACK = (0.0, -35.2, 39.4) # axis lies on x = 0, the slit's own mid-plane, and points out radially
MUZZLE_CLEARANCE_MIN = 12.0   # muzzle must stand this far clear of the dome surface
PIER_Y = (-58.0, -30.0)       # solid pier on the plate, full slit width, fused to the drum
PIER_TOP = 16.0
ARM_THICK = 4.0               # each yoke arm
ARM_INNER_X = 5.0             # arms span |x| 5.0 -> 9.0; 6.0 mm of clear air to each slit wall
ARM_GRIP = 2.0                # station along the axis where the yoke straps over the tube
ARM_RISE = 8.5                # strap height, measured perpendicular from the tube axis
ARM_KEEL = 45.0               # the keel carries the tube's underside out to its muzzle

# --------------------------------------------------------------- new counters
COUNTER_DIAMETER = 20.0       # the one preserved-list dimension this correction moves (was 16.0)
COUNTER_HEIGHT = 7.0
COUNTER_CHAMFER = 1.0
FACE_DIAMETER = COUNTER_DIAMETER - 2 * COUNTER_CHAMFER   # 18.0 flat face inside the chamfers
RIM_WIDTH = 2.0               # flat rim band, the surface a stacked pair meets on
FIELD_DIAMETER = FACE_DIAMETER - 2 * RIM_WIDTH           # 14.0
FIELD_DEPTH = 1.5             # flat field floor, 1.5 below the face
SYMBOL_DIAMETER = 12.5        # raised 1.5 back up to full face level
SYMBOL_CLEAR = (FIELD_DIAMETER - SYMBOL_DIAMETER) / 2    # 0.75 of flat floor all round
ISLAND_BEVEL = 0.3            # 45 deg bevel round the top of every raised island
WEB = COUNTER_HEIGHT - 2 * FIELD_DEPTH                   # 4.0 of solid between the two field floors

SUN_BALL_DIAMETER = 6.5
SUN_RAY_GAP = 1.0             # undisturbed ring of field between the ball and every wedge
SUN_RAY_COUNT = 8
SUN_RAY_INNER = SUN_BALL_DIAMETER / 2 + SUN_RAY_GAP      # 4.25
SUN_RAY_OUTER = SYMBOL_DIAMETER / 2                      # 6.25
SUN_RAY_INNER_WIDTH = 1.8     # narrow end, nearest the ball
SUN_RAY_TIP_WIDTH = 2.2       # blunt outer tip: the wedges widen outward

# The crescent holds two independent conditions at once: slim enough (38 % of the
# outer disc survives) and horns that wrap (the circles cross at x = +2.78, not 0).
MOON_OUTER_DIAMETER = 12.5    # concentric with the field
MOON_BITE_DIAMETER = 11.20    # smaller than the outer circle, and that is correct
MOON_BITE_OFFSET = 2.850      # centre offset along +x
MOON_TIP_FILLET = 0.45        # rounded nose, not a square cut. See GEOMETRY-NOTES.md: the
                              # brief's 0.9 mm fillet measures out at 178.6 deg of wrap with the
                              # horn tips at x = -0.07 -- the banana the host rejected. 0.45 mm is
                              # the smallest rounding that still carries the 0.3 mm island bevel
                              # and passes check_thickness at a 0.4 mm nozzle.

# SINGLE_* is the Sun counter (part keys single_01..single_12).
# FORKED_* is the Moon counter (part keys forked_01..forked_12).
BASE_COLOR = Color(0.72,0.78,0.81)
INLAY_COLOR = Color(0.12,0.16,0.32)   # night-sky indigo; the dark squares are a separate part
ROOF_COLOR = Color(0.19,0.36,0.43)
SINGLE_COLOR = Color(0.83,0.40,0.18)
FORKED_COLOR = Color(0.95,0.82,0.48)


def rounded_plate(size, height, radius):
    return extrude(RectangleRounded(size,size,radius), amount=height)


def cell_centre(c, r):
    """Board grid: zero-based file c and rank r, centre in board coordinates."""
    return (-BOARD/2 + (c+0.5)*CELL, -BOARD/2 + (r+0.5)*CELL)


def dark_cells():
    """The 32 dark squares, (file + rank) % 2 == 0, in a fixed rank-major order.

    The baseline's identity check: a1 dark, h1 light.
    """
    return [(c, r) for r in range(ROWS) for c in range(ROWS) if (c+r) % 2 == 0]


def chamfered_square(size, chamfer):
    """A square with all four PLAN corners chamfered, as an octagonal sketch.

    The chamfer is a plan cut, not a 3D edge break, because that is what leaves
    the material bridge at a diagonal pocket junction: two facing chamfer lines
    each stand chamfer/sqrt(2) back from the shared corner point, so the bridge
    between diagonally adjacent pockets is 2*chamfer/sqrt(2) wide instead of a
    zero-width non-manifold edge. Faceted rather than rounded, per the baseline
    ("prefer faceted recesses to circular ones in small detail").
    """
    h, c = size/2, chamfer
    return Polygon((-h+c,-h), (h-c,-h), (h,-h+c), (h,h-c),
                   (h-c,h), (-h+c,h), (-h,h-c), (-h,-h+c), align=None)


def build_inlay():
    """One dark square: a separate flush-seated part, printed in a contrast colour.

    Colour, not depth, is what makes this board read as a chequerboard. The
    evidence renderer shades from the surface normal alone, so two flat
    horizontal faces at different heights come out the same tone; a separate
    part in a second filament does not have that problem.
    """
    body = extrude(chamfered_square(INLAY_SIZE, INLAY_CHAMFER), amount=INLAY_THICK)
    body.label = 'inlay'
    body.color = INLAY_COLOR
    assert len(body.solids()) == 1
    return body


def build_base():
    body = rounded_plate(BASE,HEIGHT,CORNER)
    cavity = Pos(0,0,FLOOR) * Box(OPENING,OPENING,HEIGHT,align=(Align.CENTER,Align.CENTER,Align.MIN))
    body = body - cavity
    for angle in (0,90,180,270):
        opening = Pos(0,BASE/2-WALL/2,SILL_TOP)*Box(2*PIER_INNER,WALL+1,HEIGHT-SILL_TOP+1,align=(Align.CENTER,Align.CENTER,Align.MIN))
        body = body - Rot(Z=angle)*opening
    # 32 BLIND pockets, one per dark square, opening at the playing square and
    # closed by BACKING mm of continuous floor. The pocket mouth carries the same
    # plan chamfer as the inlay, which is the baseline's structural detail: without
    # it, diagonally adjacent wells share a vertical edge and the mesh is
    # non-manifold. The cut stops exactly at the floor plane, so nothing above the
    # board is touched.
    pocket = chamfered_square(POCKET_SIZE, INLAY_CHAMFER)
    for c, r in dark_cells():
        x, y = cell_centre(c, r)
        body = body - Pos(x,y,BACKING)*extrude(pocket, amount=POCKET_DEPTH)
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


def tube_axis():
    """Unit axis direction and unit upper normal of the telescope, in the YZ plane."""
    elev = math.radians(TUBE_ELEVATION)
    return (-math.cos(elev), math.sin(elev)), (math.sin(elev), math.cos(elev))


def tube_point(s, n=0.0):
    """(y, z) at s mm along the tube axis from its back face, n mm perpendicular."""
    axis, up = tube_axis()
    return (TUBE_BACK[1] + s*axis[0] + n*up[0], TUBE_BACK[2] + s*axis[1] + n*up[1])


def arm_profile():
    """Yoke arm outline in the YZ plane.

    Both feet stand on the pier. The forward edge rises well steeper than 45 deg
    to a keel that carries the tube's underside all the way to the muzzle, so no
    part of the telescope is cantilevered; the rear edge straps over the tube.
    """
    return [(PIER_Y[1], PIER_TOP), (PIER_Y[0], PIER_TOP),
            tube_point(ARM_KEEL, -TUBE_RADIUS), tube_point(ARM_GRIP, ARM_RISE)]


def build_roof():
    """Backing plate, rotation drum, exact hemisphere, shutter slit, telescope on a yoke.

    One single solid, printed plate-down with the dome apex up.
    """
    drum_top = PLATE + DRUM_HEIGHT                 # 14.7 local, z35.7 closed
    centre_z = drum_top                            # hemisphere centre sits on the drum top
    apex = centre_z + DOME_SPHERE_RADIUS           # 89.7 local, z110.7 closed
    span = 2 * DOME_SPHERE_RADIUS

    body = rounded_plate(ROOF_SIZE, PLATE, ROOF_CORNER)
    body = body + Pos(0,0,PLATE)*Cylinder(DRUM_RADIUS,DRUM_HEIGHT,align=(Align.CENTER,Align.CENTER,Align.MIN))
    cap_box = Pos(0,0,centre_z)*Box(span,span,DOME_RISE+2,align=(Align.CENTER,Align.CENTER,Align.MIN))
    body = body + (Pos(0,0,centre_z)*Sphere(DOME_SPHERE_RADIUS) & cap_box)

    ring_top = drum_top - RING_BELOW_TOP + RING_WIDTH/2
    groove = Pos(0,0,ring_top)*Cylinder(DRUM_RADIUS+2,RING_WIDTH,align=(Align.CENTER,Align.CENTER,Align.MAX)) \
           - Pos(0,0,ring_top)*Cylinder(DRUM_RADIUS-RING_DEPTH,RING_WIDTH,align=(Align.CENTER,Align.CENTER,Align.MAX))
    # Relieved upper wall. A square-cut ceiling here is an unsupported ring that
    # check_overhang fails; the relief is kept at its built absolute size.
    relief = Pos(0,0,ring_top)*Cylinder(DRUM_RADIUS+2,RING_RELIEF,align=(Align.CENTER,Align.CENTER,Align.MIN)) \
           - Pos(0,0,ring_top)*Cone(DRUM_RADIUS-RING_DEPTH,DRUM_RADIUS,RING_RELIEF,align=(Align.CENTER,Align.CENTER,Align.MIN))
    body = body - (groove + relief)

    slit = Pos(0,SLIT_FAR_Y,PLATE)*Box(SLIT_WIDTH,span,span,align=(Align.CENTER,Align.MAX,Align.MIN))
    body = body - slit

    pier = Pos(0,sum(PIER_Y)/2,PLATE)*Box(SLIT_WIDTH,PIER_Y[1]-PIER_Y[0],PIER_TOP-PLATE,align=(Align.CENTER,Align.CENTER,Align.MIN))
    # Build ONE arm, measure where it actually landed, then MIRROR it.
    #
    # The previous revision positioned both arms with hand-written offsets that
    # assumed extrude() grew the face from x=0 toward +x. It does not: build123d
    # takes the extrusion direction from the FACE NORMAL, and the face normal
    # follows the polygon's WINDING ORDER. arm_profile() winds so the normal
    # points at -x, so extrude(face, amount=4.0) spanned x = -4.000 .. 0.000 and
    # both arms came out exactly ARM_THICK off centre. Nothing here may depend on
    # which way the solid grew: the arm is placed by its MEASURED bounding box and
    # the second arm is a mirror of the first, so the pair is symmetric about
    # x = 0 by construction whatever the winding order is.
    arm_face = Plane.YZ * Polygon(*arm_profile(),align=None)
    one = extrude(arm_face,amount=ARM_THICK)
    one = Pos(ARM_INNER_X - one.bounding_box().min.X, 0, 0) * one
    arms = one + mirror(one, about=Plane.YZ)
    seat = Pos(*TUBE_BACK)*Rot(X=90-TUBE_ELEVATION)
    tube = seat*Cylinder(TUBE_RADIUS,TUBE_LENGTH,align=(Align.CENTER,Align.CENTER,Align.MIN))
    body = body + pier + arms + tube
    bore = seat*Pos(0,0,TUBE_LENGTH)*Cylinder(TUBE_BORE_RADIUS,TUBE_BORE_DEPTH,align=(Align.CENTER,Align.CENTER,Align.MAX))
    body = body - bore

    body.label = 'roof'
    body.color = ROOF_COLOR
    assert len(body.solids()) == 1
    return body


def sun_symbol():
    """An unbroken ball inside a ring of clear field, with eight detached wedges."""
    mark = Circle(SUN_BALL_DIAMETER/2)
    for i in range(SUN_RAY_COUNT):
        wedge = Polygon((SUN_RAY_INNER,-SUN_RAY_INNER_WIDTH/2),(SUN_RAY_OUTER,-SUN_RAY_TIP_WIDTH/2),
                        (SUN_RAY_OUTER,SUN_RAY_TIP_WIDTH/2),(SUN_RAY_INNER,SUN_RAY_INNER_WIDTH/2),align=None)
        mark = mark + Rot(Z=i*360/SUN_RAY_COUNT)*wedge
    # Hold the whole mark inside the Ø12.5 symbol circle, so the 0.75 mm of clear
    # field survives at the wedge tip corners as well as along their flat ends.
    return mark & Circle(SYMBOL_DIAMETER/2)


def moon_symbol():
    """One slim crescent whose horns curl past the middle, both tips rounded."""
    crescent = Circle(MOON_OUTER_DIAMETER/2) - Pos(MOON_BITE_OFFSET,0)*Circle(MOON_BITE_DIAMETER/2)
    return fillet(crescent.vertices(), MOON_TIP_FILLET)


def build_counter(forked=False):
    """A round draughts disc carrying the same raised mark on both faces.

    Rim band, field floor and symbol top are the same on each side and the two
    faces are mirror images, so there is no wrong way up and two counters stack
    rim-band to rim-band.
    """
    body = extrude(Circle(COUNTER_DIAMETER/2),amount=COUNTER_HEIGHT)
    body = chamfer(body.edges().filter_by(GeomType.CIRCLE),length=COUNTER_CHAMFER)
    mark = moon_symbol() if forked else sun_symbol()
    island = extrude(mark,amount=FIELD_DEPTH)
    island = chamfer(island.edges().group_by(Axis.Z)[-1],length=ISLAND_BEVEL)
    sunk = Pos(0,0,COUNTER_HEIGHT-FIELD_DEPTH)*(extrude(Circle(FIELD_DIAMETER/2),amount=FIELD_DEPTH) - island)
    body = body - sunk - Pos(0,0,COUNTER_HEIGHT)*mirror(sunk,Plane.XY)
    body.label = 'moon_counter' if forked else 'sun_counter'
    body.color = FORKED_COLOR if forked else SINGLE_COLOR
    assert len(body.solids()) == 1
    return body
