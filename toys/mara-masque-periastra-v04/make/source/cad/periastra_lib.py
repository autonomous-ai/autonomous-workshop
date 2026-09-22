"""Periastra Zenith design library, revision D: the telescope stands on the floor.

This revision corrects exactly one thing -- the telescope and the way the dome
carries it -- and changes nothing else in the object.

The shipped roof took the tube out of the dome 55 degrees from the apex, only 35
degrees above the springing line, and stood 11.9 mm of barrel in the open air:
a spout. It carried the tube on a two-armed yoke whose keel and rectangular foot
block sat in a 30 mm channel cut clean through the drum wall, which broke the
rotation ring -- the one part of a real dome that is continuous by definition,
because the dome turns on it.

Revision D does three things, and they are one change:

A. THE SLIT STOPS AT THE SPRINGING LINE. It still runs the full height of the
   dome -- from its far edge, over the apex, down the near flank to the bottom
   of the dome -- but its lower limit is now z 14.7, the drum top, instead of
   z 3.0. The drum below it is whole and its rotation-ring groove runs unbroken
   all the way round. The slit's floor is the exposed drum top: the observatory
   floor.

B. THE TELESCOPE STANDS ON THAT FLOOR. The tube is 87.0 mm long on an axis 50
   degrees above horizontal, meeting the floor plane at (0, +13.0, 14.7), where
   the floor plane itself cuts it off flat on a level 15.0 x 19.58 mm elliptical
   foot fused to the drum. It leaves the dome 32.4 degrees from the apex and its
   mouth stands a few millimetres proud of the shell. 50 degrees is a hard
   floor: the steepest downward-facing surface of a cylinder inclined E degrees
   above horizontal has its normal E degrees from vertical, so at the shipped 35
   degrees the tube was a 35-degree overhang and needed the keel. At 50 it
   clears the 45-degree gate by 5 degrees and needs nothing under its length.

C. THE OLD MOUNT IS GONE. No fork, no arms, no keel, no pier, no foot block.
   Above the floor the only thing standing in the slit is the telescope, and the
   root where it meets the floor is blended with a 6.0 mm cove fillet carried
   right round the foot, because that root is a cantilever taken entirely in the
   weak direction of the layer lines.

FOUR of the five print designs are FROZEN: base, inlay, sun counter and moon
counter. `measure/check_fit.py` asserts all four published sha256 values on
every run and fails the build if any of them moves.
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

# The slit cuts the DOME only. Its lower limit is the drum top, which is also the
# dome's springing line and the sphere's centre height. Below it the drum is
# whole and the rotation ring runs unbroken all the way round.
SLIT_FLOOR_Z = PLATE + DRUM_HEIGHT   # 14.7 local, z35.7 closed (was 3.0, the plate top)

# Telescope: diameter, bore and bore depth are exactly what the shipped roof
# proved. Its length, elevation and footing are what this revision re-solves.
TUBE_RADIUS = 7.5             # 15.0 mm outer diameter
TUBE_BORE_RADIUS = 3.5        # 7.0 mm muzzle bore -> 4.0 mm tube wall
TUBE_BORE_DEPTH = 13.0        # blind, >= 12.0
TUBE_LENGTH = 85.3            # along the axis, FROM THE FLOOR PLANE (was 45.0 on a yoke)
TUBE_ELEVATION = 50.0         # degrees above horizontal, in the YZ plane (was 35.0)
TUBE_ELEVATION_MIN = 45.0     # hard floor: below it the tube is an overhang and the keel returns
TUBE_FOOT = (0.0, 13.0, SLIT_FLOOR_Z)  # where the axis meets the observatory floor.
                              # The brief's free window is y +13.0 to +18.0 and this is its
                              # low end: the smaller y is, the nearer the tube's axis passes
                              # to the sphere's own centre, so the tube leaves the shell more
                              # radially and less of its flank stands in the open.
TUBE_STUB = 10.0              # the tube is built through the floor plane and cut off BY it;
                              # long enough that its raw end face is wholly under the floor
TUBE_COVE = 6.0               # cove fillet radius at the root; the brief's floor is 6.0
COVE_PAD_Y = 30.0             # half-length of the drum-top block the cove runs out onto
MUZZLE_PROJECTION_MIN = 2.5   # the mouth must clear the shell, but only just
MUZZLE_PROJECTION_MAX = 7.0   # above this it is the cannon the critic named

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
    """(y, z) at s mm along the tube axis from its FOOT, n mm perpendicular.

    s = 0 is the point where the axis meets the observatory floor at z 14.7;
    s = TUBE_LENGTH is the centre of the muzzle face.
    """
    axis, up = tube_axis()
    return (TUBE_FOOT[1] + s*axis[0] + n*up[0], TUBE_FOOT[2] + s*axis[1] + n*up[1])


def tube_foot_ellipse():
    """Minor and major axis of the level elliptical foot the floor plane cuts.

    The floor plane is horizontal and the axis is TUBE_ELEVATION above it, so the
    cut is an ellipse 2*TUBE_RADIUS across the slit and 2*TUBE_RADIUS/sin(elev)
    along it.
    """
    return 2*TUBE_RADIUS, 2*TUBE_RADIUS/math.sin(math.radians(TUBE_ELEVATION))


def build_roof():
    """Backing plate, rotation drum, exact hemisphere, shutter slit, standing telescope.

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

    # The shutter slit cuts the DOME ONLY. It runs the full height of the dome --
    # from its far edge at SLIT_FAR_Y, over the apex, and down the near flank to
    # the bottom of the dome -- but it stops at the springing line, so the drum
    # below keeps its wall and its rotation ring all the way round. The floor it
    # leaves behind is the exposed drum top: a level rectangle SLIT_WIDTH across,
    # bounded in y by the drum's own circle.
    assert math.isclose(SLIT_FLOOR_Z, drum_top, abs_tol=1e-9)
    slit = Pos(0,SLIT_FAR_Y,SLIT_FLOOR_Z)*Box(SLIT_WIDTH,span,span,align=(Align.CENTER,Align.MAX,Align.MIN))
    body = body - slit

    # THE TELESCOPE IS ITS OWN PIER.
    #
    # The dome is a solid hemisphere and the slit is a box that removes every
    # piece of material inside it, so nothing solid touches the tube anywhere
    # along its length. There is exactly one piece of material it can reach
    # without a bracket -- the floor of the slit -- so it is made long enough to
    # stand on it, and the fork, the keel and the foot block are deleted. That is
    # also how a real observatory is built: the instrument stands on its own
    # footing on the observatory floor and the dome turns around it.
    #
    # The tube is built THROUGH the floor plane and cut off flat BY it. `pad` is
    # the block of drum material the root sits on; it is wholly inside the drum
    # that is already there, so fusing it adds nothing outside the tube and its
    # cove, and it gives the fillet a face to run out onto.
    seat = Pos(*TUBE_FOOT)*Rot(X=90-TUBE_ELEVATION)
    raw = seat*Pos(0,0,-TUBE_STUB)*Cylinder(TUBE_RADIUS,TUBE_LENGTH+TUBE_STUB,
                                            align=(Align.CENTER,Align.CENTER,Align.MIN))
    pad = Box(SLIT_WIDTH,2*COVE_PAD_Y,SLIT_FLOOR_Z,align=(Align.CENTER,Align.CENTER,Align.MIN))
    assert math.hypot(SLIT_WIDTH/2,COVE_PAD_Y) < DRUM_RADIUS - RING_DEPTH
    # THE ROOT IS THE WEAK POINT. 87 mm of tube is cantilevered off a
    # 15.0 x 19.6 mm foot with its centre of mass 18.2 mm outside that foot, and
    # in FDM the layer lines at the root run across the bending plane. A bare butt
    # joint would snap there, so the whole foot is blended into the floor with a
    # cove of radius TUBE_COVE. The cove's run onto the floor is r/tan(theta/2)
    # for a dihedral theta, which is widest on the downhill side of the foot; the
    # built extents are measured in measure/check_fit.py, not assumed here.
    root = pad + raw
    cove = root.edges().filter_by(GeomType.ELLIPSE) \
                   .filter_by_position(Axis.Z, SLIT_FLOOR_Z-1e-6, SLIT_FLOOR_Z+1e-6)
    assert len(cove) >= 1, 'the tube/floor junction ellipse was not found'
    root = fillet(cove, TUBE_COVE)
    body = body + root
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
