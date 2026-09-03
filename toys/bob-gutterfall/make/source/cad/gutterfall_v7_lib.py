"""Parametric one-piece Gutterfall geometry, dimensions in millimetres."""
from build123d import Box, Cylinder, Cone, Sphere, Torus, Pos, Rot, Align, Axis, fillet

OVERALL_LENGTH = 105.0
WING_SPAN = 88.0
THROAT_CLEARANCE = 31.0
BELLY_RADIUS = 18.0
TAIL_PAD_LENGTH = 24.0
TAIL_PAD_WIDTH = 34.0
TAIL_PAD_THICKNESS = 7.0


def ellipsoid(rx, ry, rz, x, y, z):
    return Pos(x, y, z) * Sphere(1).scale((rx, ry, rz))


def build_gargoyle():
    # Torso and rolling belly form one broad convex upper jaw.
    body = ellipsoid(31, 22, 18, 13, 0, 38)
    belly = Pos(-1, 0, 38) * Rot(90, 0, 0) * Cylinder(
        BELLY_RADIUS, 40, align=(Align.CENTER, Align.CENTER, Align.CENTER))

    # Head, muzzle, brows, blunt horns, and crouched forelimbs.
    # These overlaps are intentionally generous: every character mass is a
    # true part of the load-bearing body, not a merely tangent mesh shell.
    head = ellipsoid(17, 17, 14, 35, 0, 43)
    muzzle = ellipsoid(12, 15, 8, 47, 0, 39)
    brow_l = ellipsoid(8, 6, 5, 43, -7, 48)
    brow_r = ellipsoid(8, 6, 5, 43, 7, 48)
    horn_l = ellipsoid(7, 6, 10, 31, -10, 52)
    horn_r = ellipsoid(7, 6, 10, 31, 10, 52)
    fore_l = ellipsoid(15, 10, 9, 30, -12, 27)
    fore_r = ellipsoid(15, 10, 9, 30, 12, 27)
    paw_l = ellipsoid(11, 8, 6, 39, -13, 21)
    paw_r = ellipsoid(11, 8, 6, 39, 13, 21)

    # Swept solid wings: rounded, thick masses rather than plate-like slabs.
    wing_l = Pos(0, -27, 49) * Box(
        54, 30, 10, align=(Align.CENTER, Align.CENTER, Align.CENTER))
    wing_r = Pos(0, 27, 49) * Box(
        54, 30, 10, align=(Align.CENTER, Align.CENTER, Align.CENTER))
    wing_l = fillet(wing_l.edges(), radius=4)
    wing_r = fillet(wing_r.edges(), radius=4)

    # Thick open C-tail: rear bridge, descending haunch, and forward underside pad.
    tail_root = ellipsoid(18, 17, 14, -18, 0, 38)
    rear = Pos(-37, 0, 17) * Cylinder(16, 34)
    rear_round = ellipsoid(10, 17, 13, -35, 0, 14)
    stop = Pos(-19, 0, 3.5) * Box(TAIL_PAD_LENGTH + 14, TAIL_PAD_WIDTH, TAIL_PAD_THICKNESS,
                                  align=(Align.CENTER, Align.CENTER, Align.CENTER))
    stop_nose = ellipsoid(8, 17, 4, 0, 0, 4)
    throat_bridge = Pos(1, 0, 21) * Box(12, 34, 34,
                                       align=(Align.CENTER, Align.CENTER, Align.CENTER))
    cheek_bridge = ellipsoid(16, 22, 12, 10, 0, 25)

    # Explicit Boolean fusion removes internal coincident skins before mesh
    # export; additive compounds can look joined while retaining extra shells.
    shape = body
    for mass in (
        belly, head, muzzle, brow_l, brow_r, horn_l, horn_r, fore_l, fore_r,
        paw_l, paw_r, wing_l, wing_r, tail_root, rear, rear_round, stop,
        stop_nose, throat_bridge, cheek_bridge,
    ):
        shape = shape.fuse(mass)
    # A single visible, full-width mouth receives the furniture edge from the
    # rear.  The cutter exits both side faces and the tail end, producing a
    # truthful C-profile rather than a hidden internal pocket.  Its 31 mm
    # vertical opening admits the specified 18--28 mm furniture edges.
    throat = Pos(-49, 0, 22.5) * Box(
        80, 50, THROAT_CLEARANCE,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    throat = fillet(throat.edges(), radius=2)
    shape = shape - throat
    # Re-unite the front and rear load paths over the full-height mouth cut.
    # This dorsal saddle remains above the 31 mm furniture clearance.
    dorsal_saddle = ellipsoid(20, 18, 7, 9, 0, 44)
    tail_roof = Pos(-31, 0, 42) * Box(
        46, 38, 8,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    tail_roof = fillet(tail_roof.edges(), radius=2)
    shape = shape.fuse(dorsal_saddle).fuse(tail_roof).clean()
    assert len(shape.solids()) == 1, "Gutterfall must remain one printable solid"
    # Canonical print orientation: the broad underside pad sits on Z=0.
    return shape
