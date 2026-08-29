"""Parametric geometry for Lantern Menagerie.

All four part builders return broad-face-down printable solids.  The assembly
builder places them in the functional gate pose.  Dimensions are millimetres.
"""

from __future__ import annotations

import math

import cadfits
from build123d import (
    Align,
    Axis,
    Box,
    BuildSketch,
    Circle,
    Compound,
    Cylinder,
    Ellipse,
    Mode,
    Plane,
    Polygon,
    Pos,
    RectangleRounded,
    Rot,
    SlotOverall,
    Vector,
    extrude,
)
from cadgen.assembly import AssemblyHelper


# Sealed optical and envelope dimensions [invented.json].
REEL_D = 114.0
REEL_T = 3.2
REEL_OUTER_R = REEL_D / 2
REEL_RING_INNER_R = 55.0
REEL_HUB_R = 7.0
PORTAL_D = 44.0
PORTAL_R = PORTAL_D / 2
PORTAL_Y = 31.0
CREATURE_PITCH_R = 31.0
SHELL_FACE_T = 2.4
AXIAL_GAP = 0.30
FRONT_INNER_Z = SHELL_FACE_T
REEL_Z = FRONT_INNER_Z + AXIAL_GAP
REAR_INNER_Z = REEL_Z + REEL_T + AXIAL_GAP
ASSEMBLY_DEPTH = REAR_INNER_Z + SHELL_FACE_T

# Frame adjusted inside the sealed maximum so the 114 mm reel clears the bed.
FRAME_BOTTOM_Y = -59.0
FRAME_TOP_Y = 60.0
FRAME_BASE_W = 108.0
FRAME_BASE_H = 19.0
FRAME_BASE_CY = FRAME_BOTTOM_Y + FRAME_BASE_H / 2
ARCH_OUTER_R = 32.0
PILLAR_W = 8.0
PILLAR_H = 62.0
PILLAR_CY = -9.0
AXLE_BRIDGE_W = 58.0
AXLE_BRIDGE_H = 12.0

# Fits derive the male from the female once, through cadfits.
SPINDLE_BORE_D = 7.8
SPINDLE_D = cadfits.peg_for(SPINDLE_BORE_D, 0.30)
# The spindle crosses the reel and seats 1.2 mm into a 1.5 mm blind rear bore,
# leaving 0.3 mm end clearance and a continuous 0.9 mm rear wall.
SPINDLE_LEN = REAR_INNER_Z - SHELL_FACE_T + 1.2
HOOK_W = 3.2
HOOK_H = 5.0
HOOK_SLOT_W = cadfits.slot_for(HOOK_W, "slip")
HOOK_SLOT_H = cadfits.slot_for(HOOK_H, "slip")
HOOK_STEM_LEN = ASSEMBLY_DEPTH - SHELL_FACE_T
HOOK_BARB_T = 1.0
HOOK_POSITIONS = ((-43.0, -49.0), (43.0, -49.0), (-15.0, 59.0), (15.0, 59.0))

# Stand geometry and pose.  112 degrees from folded-up gives 68 degrees rear
# of the downward gate plane and a foot near the table datum.
STAND_W = 74.0
STAND_L = 88.0
STAND_T = 5.0
STAND_BODY_T = 4.6
STAND_BODY_Z = 1.2
STAND_ARM_W = 6.0
STAND_BAR_H = 10.0
TRUNNION_D = 6.0
TRUNNION_R = TRUNNION_D / 2
TRUNNION_LEN = 19.0
TRUNNION_SOCKET_D = cadfits.slot_for(TRUNNION_D, "slip")
STAND_HINGE_X = 52.5
STAND_HINGE_Y = -30.5
STAND_HINGE_Z = 14.5
STAND_DEPLOY_DEG = 108.0
TRUNNION_Y = 5.0
BEARING_BLOCK_W = 8.0
BEARING_BLOCK_H = 12.0
BEARING_SOCKET_R = 3.35

# Deliberate print margins, not physical strength proof.
MIN_WEB = 3.2
SPOKE_W = 5.0
EDGE_R = 1.5


def _sketch_disk(radius: float, height: float):
    with BuildSketch(Plane.XY) as sketch:
        Circle(radius)
    return extrude(sketch.sketch, amount=height)


def _sketch_ellipse(rx: float, ry: float, height: float):
    with BuildSketch(Plane.XY) as sketch:
        Ellipse(rx, ry)
    return extrude(sketch.sketch, amount=height)


def _sketch_polygon(points: list[tuple[float, float]], height: float):
    with BuildSketch(Plane.XY) as sketch:
        Polygon(*points)
    return extrude(sketch.sketch, amount=height)


def _rounded_plate(width: float, height: float, radius: float, thickness: float):
    with BuildSketch(Plane.XY) as sketch:
        RectangleRounded(width, height, radius)
    return extrude(sketch.sketch, amount=thickness)


def _bar_between(a: tuple[float, float], b: tuple[float, float], width: float, height: float):
    ax, ay = a
    bx, by = b
    length = math.hypot(bx - ax, by - ay)
    angle = math.degrees(math.atan2(by - ay, bx - ax))
    bar = Box(length, width, height, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return Pos((ax + bx) / 2, (ay + by) / 2, 0) * Rot(0, 0, angle) * bar


def _capsule(a: tuple[float, float], b: tuple[float, float], width: float, height: float):
    ax, ay = a
    bx, by = b
    length = math.hypot(bx - ax, by - ay) + width
    angle = math.degrees(math.atan2(by - ay, bx - ax))
    with BuildSketch(Plane.XY) as sketch:
        SlotOverall(length, width, rotation=angle)
    return Pos((ax + bx) / 2, (ay + by) / 2, 0) * extrude(sketch.sketch, amount=height)


def _fuse_all(shapes):
    result = shapes[0]
    for shape in shapes[1:]:
        result = result.fuse(shape)
    return result


def _frame_face(thickness: float):
    # A 54 mm moon disk masks inactive features while exposing 3 mm of the
    # scalloped wheel around its circumference.  The deeply overlapping top
    # cap supplies a robust portal crown without knife-edge circle unions.
    face = _sketch_disk(54.0, thickness)
    top_cap = Pos(0, 52.0, 0) * _rounded_plate(50.0, 24.0, 10.0, thickness)
    base = Pos(0, FRAME_BASE_CY, 0) * _rounded_plate(FRAME_BASE_W, FRAME_BASE_H, 4.0, thickness)
    shield = _fuse_all([face, top_cap, base])
    return shield.cut(Pos(0, PORTAL_Y, -0.5) * _sketch_disk(PORTAL_R, thickness + 1.0))


def _axis_x_cylinder(x0: float, y: float, z: float, radius: float, length: float):
    """Cylinder with an explicit +X axis, used for the split stand bearing."""
    return Pos(x0, y, z) * Rot(0, 90, 0) * Cylinder(
        radius, length, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )


def _rear_bearing_support(shell):
    """Add two rear-plane blind bearings outside the wheel envelope."""
    for side in (-1.0, 1.0):
        x = side * STAND_HINGE_X
        rib = _bar_between(
            (side * 48.0, -47.0), (x, STAND_HINGE_Y), 6.0, SHELL_FACE_T
        )
        cheek = Pos(x, STAND_HINGE_Y, 0) * Box(
            BEARING_BLOCK_W, BEARING_BLOCK_H,
            STAND_HINGE_Z - REAR_INNER_Z + BEARING_SOCKET_R + 1.05,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        socket_x0 = x - BEARING_BLOCK_W / 2 if side > 0 else x - BEARING_BLOCK_W / 2 + 1.0
        socket = _axis_x_cylinder(
            socket_x0,
            STAND_HINGE_Y,
            STAND_HINGE_Z - REAR_INNER_Z,
            BEARING_SOCKET_R,
            BEARING_BLOCK_W - 1.0,
        )
        # Each bore is open only on its inward X face and blind at the outer
        # wall.  The long U arms flex inward for one-time trunnion insertion,
        # then expand into the bores and retain the stand without a loose cap.
        shell = shell.fuse(rib, cheek).cut(socket)
    return shell


def make_front_shell():
    shell = _frame_face(SHELL_FACE_T)
    spindle = Pos(0, 0, SHELL_FACE_T) * Cylinder(
        SPINDLE_D / 2, SPINDLE_LEN,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    shell = shell.fuse(spindle)
    for x, y in HOOK_POSITIONS:
        stem = Pos(x, y, SHELL_FACE_T) * Box(
            HOOK_W, HOOK_H, HOOK_STEM_LEN,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        barb = Pos(x, y, SHELL_FACE_T + HOOK_STEM_LEN) * Box(
            HOOK_W + 1.0, HOOK_H + 1.0, HOOK_BARB_T,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        shell = shell.fuse(stem, barb)
    # A real coplanar 6 x 16 mm leaf is isolated on three sides in the front
    # base.  Its nose enters front-face index pockets without a rigid boss in
    # the wheel sweep.
    for x in (-3.7, 3.7):
        shell = shell.cut(Pos(x, -50.0, -0.1) * Box(
            1.4, 16.0, SHELL_FACE_T + 0.2,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        ))
    # The broad opening that releases the leaf also forms the fixed shell
    # reset index directly beneath the reel's double-V.
    shell = shell.cut(Pos(0, -59.0, -0.1) * Box(
        8.8, 2.0, SHELL_FACE_T + 0.2,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    ))
    nose = Pos(0, -52.5, SHELL_FACE_T) * Cylinder(
        1.5, 0.65, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    shell = shell.fuse(nose)
    shell.label = "front_shell"
    assert len(shell.solids()) == 1
    return shell


def make_rear_shell():
    shell = _rear_bearing_support(_frame_face(SHELL_FACE_T))
    # The elevated hinge keeps both integral pins entirely behind the optical
    # face, preserving a continuous, full-thickness rear mask.
    # A 24-sided bore keeps the specified 7.8 mm minimum diameter while
    # avoiding a mesh-scale curved-rim sliver at the print datum.
    bore_apothem = SPINDLE_BORE_D / 2
    bore_radius = bore_apothem / math.cos(math.pi / 24)
    bore_points = [
        (
            math.cos(2 * math.pi * index / 24) * bore_radius,
            math.sin(2 * math.pi * index / 24) * bore_radius,
        )
        for index in range(24)
    ]
    bore = Pos(0, 0, -0.5) * _sketch_polygon(bore_points, 2.0)
    shell = shell.cut(bore)
    for x, y in HOOK_POSITIONS:
        slot = Pos(x, y, -0.5) * Box(
            HOOK_SLOT_W, HOOK_SLOT_H, SHELL_FACE_T + 1.0,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        shell = shell.cut(slot)
    # Rear aiming ticks stay outside the light path; portal-edge bites are the
    # projected symmetry cue.  Full concentric rings would obstruct the portal.
    for angle in (0, 90, 180, 270):
        rad = math.radians(angle)
        tick = Pos(
            math.cos(rad) * 26.0,
            PORTAL_Y + math.sin(rad) * 26.0,
            SHELL_FACE_T,
        ) * Rot(0, 0, angle) * Box(5.0, 2.2, 0.8, align=(Align.CENTER, Align.CENTER, Align.MIN))
        shell = shell.fuse(tick)
    # Two small opaque portal-edge bites provide a projected bilateral
    # alignment cue; all other aiming decoration remains blind relief.
    for x in (-PORTAL_R + 1.5, PORTAL_R - 1.5):
        shell = shell.fuse(Pos(x, PORTAL_Y, 0) * Box(
            3.0, 5.0, SHELL_FACE_T + 0.2,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        ))
    shell.label = "rear_shell"
    assert len(shell.solids()) == 1
    return shell


def _rabbit(height: float):
    shapes = [
        Pos(-3, -5, 0) * _sketch_ellipse(11, 10, height),
        Pos(7, 5, 0) * _sketch_ellipse(7, 6, height),
        Pos(13, 3, 0) * _sketch_ellipse(4, 3, height),
        Pos(-14, -4, 0) * _sketch_disk(4, height),
        _capsule((3, 9), (0, 21), 4.8, height),
        _capsule((8, 9), (8, 21), 4.5, height),
        _bar_between((-9, -13), (-9, -25.5), 3.6, height),
        _bar_between((4, -13), (4, -25.5), 3.6, height),
    ]
    return _fuse_all(shapes)


def _fox(height: float):
    shapes = [
        Pos(2, -6, 0) * _sketch_ellipse(12, 7, height),
        _capsule((-6, -3), (-10, 4), 7, height),
        Pos(-11, 5, 0) * _sketch_ellipse(10, 7, height),
        _capsule((-11, 8), (-10, 19), 4.5, height),
        _capsule((-6, 8), (-3, 17), 4.5, height),
        _capsule((9, -5), (17, 6), 10.0, height),
        _bar_between((-3, -11), (-3, -25.5), 3.8, height),
        _bar_between((7, -11), (7, -25.5), 3.8, height),
    ]
    return _fuse_all(shapes)


def _owl(height: float):
    shapes = [
        Pos(0, -5, 0) * _sketch_ellipse(11, 15, height),
        Pos(0, 8, 0) * _sketch_disk(10, height),
        _capsule((-7, 12), (-7, 20), 4.0, height),
        _capsule((7, 12), (7, 20), 4.0, height),
        Pos(-8, -4, 0) * _sketch_ellipse(5, 11, height),
        Pos(8, -4, 0) * _sketch_ellipse(5, 11, height),
        _capsule((-21, -20), (21, -20), 3.6, height),
        _bar_between((-4, -12), (-4, -20), 4.0, height),
        _bar_between((4, -12), (4, -20), 4.0, height),
        _bar_between((0, -20), (0, -25.5), 4.0, height),
    ]
    return _fuse_all(shapes)


def make_shadow_reel():
    # One continuous twelve-lobed perimeter supplies the sealed shallow grip
    # scallops without circle-cut cusp slivers.  Maxima remain exactly 57 mm.
    outer_points = []
    for index in range(144):
        angle = 2 * math.pi * index / 144
        radius = 56.6 + 0.4 * math.cos(12 * angle)
        outer_points.append((math.cos(angle) * radius, math.sin(angle) * radius))
    outer = _sketch_polygon(outer_points, REEL_T)
    inner = _sketch_disk(REEL_RING_INNER_R, REEL_T + 1.0)
    ring = outer.cut(Pos(0, 0, -0.5) * inner)
    hub = _sketch_disk(REEL_HUB_R, REEL_T)
    shapes = [ring, hub]
    for angle in (30.0, 150.0, 270.0):
        rad = math.radians(angle)
        shapes.append(_bar_between(
            (0.0, 0.0),
            (math.cos(rad) * 58.0, math.sin(rad) * 58.0),
            SPOKE_W,
            REEL_T,
        ))
    # Dedicated front-face detent pads bridge broadly into the carrier rather
    # than cutting pockets through the narrow 55--57 mm annulus.
    for angle in (-90.0, 30.0, 150.0):
        rad = math.radians(angle)
        shapes.append(Pos(math.cos(rad) * 52.5, math.sin(rad) * 52.5, 0) * _sketch_disk(3.8, REEL_T))
    for animal, angle in ((_rabbit(REEL_T), 0.0), (_fox(REEL_T), 120.0), (_owl(REEL_T), 240.0)):
        placed = Pos(0, CREATURE_PITCH_R, 0) * animal
        shapes.append(Rot(0, 0, angle) * placed)
    reel = _fuse_all(shapes).intersect(outer).first
    bore = Pos(0, 0, -0.5) * Cylinder(
        SPINDLE_BORE_D / 2, REEL_T + 1.0,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    reel = reel.cut(bore)
    # At rabbit home, the two smooth perimeter valleys flanking the downward
    # lobe provide the paired reset-V cue against the fixed shell pointer.
    # Three blind pockets open toward the front leaf; rabbit is visibly deeper.
    for angle, depth in ((-90.0, 0.85), (30.0, 0.60), (150.0, 0.60)):
        rad = math.radians(angle)
        pocket = Pos(math.cos(rad) * 52.5, math.sin(rad) * 52.5, -0.1) * Cylinder(
            1.5, depth + 0.1,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        reel = reel.cut(pocket)
    reel.label = "shadow_reel"
    assert len(reel.solids()) == 1
    return reel


def make_kickstand():
    # A true U: two narrow arms joined only by the broad rear foot.  Omitting a
    # top crossbar keeps every stand member outside the reel and shell pillars.
    arm_length = STAND_L - TRUNNION_Y
    arm_center_y = TRUNNION_Y + arm_length / 2
    left_arm = Pos(-STAND_W / 2 + STAND_ARM_W / 2, arm_center_y, STAND_BODY_Z) * _rounded_plate(
        STAND_ARM_W, arm_length, 2.0, STAND_BODY_T
    )
    right_arm = Pos(STAND_W / 2 - STAND_ARM_W / 2, arm_center_y, STAND_BODY_Z) * _rounded_plate(
        STAND_ARM_W, arm_length, 2.0, STAND_BODY_T
    )
    foot = Pos(0, STAND_L - STAND_BAR_H / 2, STAND_BODY_Z) * _rounded_plate(
        STAND_W, STAND_BAR_H, 3.0, STAND_BODY_T
    )
    # Full-height rectangular root lugs carry the trunnions into the rounded
    # arms without leaving a mesh-scale wedge at either arm end.
    left_lug = Pos(-STAND_W / 2 + STAND_ARM_W / 2, TRUNNION_Y, 0) * Box(
        STAND_ARM_W, 8.0, 6.0,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    right_lug = Pos(STAND_W / 2 - STAND_ARM_W / 2, TRUNNION_Y, 0) * Box(
        STAND_ARM_W, 8.0, 6.0,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    stand = _fuse_all([left_arm, right_arm, foot, left_lug, right_lug])
    # Printable octagonal trunnions: 6 mm across the principal axes, broad
    # horizontal/vertical facets, and 0.35 mm nominal socket clearance.
    pin_profile = [
        (TRUNNION_Y - 3.0, 1.7),
        (TRUNNION_Y - 1.3, 0.0),
        (TRUNNION_Y + 1.3, 0.0),
        (TRUNNION_Y + 3.0, 1.7),
        (TRUNNION_Y + 3.0, 4.3),
        (TRUNNION_Y + 1.3, 6.0),
        (TRUNNION_Y - 1.3, 6.0),
        (TRUNNION_Y - 3.0, 4.3),
    ]
    with BuildSketch(Plane.YZ.offset(-STAND_W / 2 + 2.0)) as left_sketch:
        Polygon(*pin_profile)
    left_pin = extrude(left_sketch.sketch, amount=-TRUNNION_LEN)
    with BuildSketch(Plane.YZ.offset(STAND_W / 2 - 2.0)) as right_sketch:
        Polygon(*pin_profile)
    right_pin = extrude(right_sketch.sketch, amount=TRUNNION_LEN)
    stand = stand.fuse(left_pin, right_pin)
    stand.label = "kickstand"
    assert len(stand.solids()) == 1
    return stand


def make_assembly(reel_angle_deg: float = 0.0, stand_deployed: bool = True):
    asm = AssemblyHelper("lantern_menagerie")
    upright = Pos(0, 0, -FRAME_BOTTOM_Y) * Rot(90, 0, 0)
    asm.add(upright * make_front_shell(), "front_shell")
    # Public state angles are clockwise as viewed from the front; build123d's
    # positive Z rotation is counter-clockwise, hence the explicit sign.
    wheel = Pos(0, 0, REEL_Z) * Rot(0, 0, -reel_angle_deg) * make_shadow_reel()
    asm.add(upright * wheel, "shadow_reel")
    # Flip only the thickness axis; a 180-degree X rotation would also mirror
    # the portal vertically and break the light path.
    rear = Pos(0, 0, REAR_INNER_Z) * make_rear_shell()
    asm.add(upright * rear, "rear_shell")
    stand = make_kickstand()
    if stand_deployed:
        stand = Pos(0, STAND_HINGE_Y, STAND_HINGE_Z) * Rot(STAND_DEPLOY_DEG, 0, 0) * Pos(0, -TRUNNION_Y, -3.0) * stand
    else:
        stand = Pos(0, STAND_HINGE_Y - TRUNNION_Y, STAND_HINGE_Z - 3.0) * stand
    asm.add(upright * stand, "kickstand")
    return asm.build()


def parameter_audit() -> dict[str, float | int]:
    return {
        "part_count": 4,
        "reel_diameter_mm": REEL_D,
        "portal_diameter_mm": PORTAL_D,
        "portal_offset_mm": PORTAL_Y,
        "spindle_diameter_mm": SPINDLE_D,
        "spindle_bore_diameter_mm": SPINDLE_BORE_D,
        "spindle_radial_clearance_mm": (SPINDLE_BORE_D - SPINDLE_D) / 2,
        "axial_gap_each_side_mm": AXIAL_GAP,
        "min_web_mm": MIN_WEB,
        "stand_deploy_rotation_deg": STAND_DEPLOY_DEG,
        "frame_height_mm": FRAME_TOP_Y - FRAME_BOTTOM_Y,
    }


assert math.isclose(SPINDLE_D, 7.2, abs_tol=1e-9)
assert math.isclose(REAR_INNER_Z - (REEL_Z + REEL_T), AXIAL_GAP, abs_tol=1e-9)
assert FRAME_TOP_Y - FRAME_BOTTOM_Y <= 130.0
assert REEL_D <= 114.0
