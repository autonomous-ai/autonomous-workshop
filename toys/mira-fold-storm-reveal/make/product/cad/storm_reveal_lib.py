"""Shared parametric geometry for the Storm Reveal three-part puzzle."""

from __future__ import annotations

import math

from build123d import (
    Align,
    Axis,
    Box,
    BuildLine,
    BuildSketch,
    CenterArc,
    Circle,
    Compound,
    Cylinder,
    Location,
    Mode,
    Plane,
    Polygon,
    Pos,
    Rot,
    SlotArc,
    extrude,
)
import cadfits

# Keep exported CAD monochrome.  The OpenCascade STEP writer emits multiple
# presentation-colour records in process-dependent order, which made a fresh
# isolated rebuild alternate between two byte sequences despite identical
# geometry.  Shape, labels, and separate occurrences carry the design intent.


# Envelope and print process [assumed from the pocket-size Wish].
NOZZLE_D = 0.40
CLOUD_THICKNESS = 6.0
MOTIF_THICKNESS = 3.0
FACE_GAP = 0.40
PIVOT_X = 0.0
PIVOT_Y = 11.0
DEPLOY_ANGLE_DEG = 90.0

# Mating system [derived; do not size both halves independently].
DRIVE_SQUARE = 5.0
LIGHTNING_SOCKET = cadfits.slot_for(DRIVE_SQUARE, 0.10)
PIVOT_RADIAL_CLEARANCE = 0.30
PIVOT_BORE_D = math.sqrt(2.0) * DRIVE_SQUARE + 2.0 * PIVOT_RADIAL_CLEARANCE
GUIDE_PIN_D = 3.2
GUIDE_SLOT_W = cadfits.slot_for(GUIDE_PIN_D, 0.20)
GUIDE_RADIUS = 11.0
PIVOT_POCKET_DEPTH = 4.2
GUIDE_SLOT_DEPTH = 3.4

# Rotor stack, in assembly Z.
LIGHTNING_Z = -(MOTIF_THICKNESS + FACE_GAP)
RAINBOW_Z = -(2.0 * MOTIF_THICKNESS + 2.0 * FACE_GAP)
DRIVE_LOCAL_START_Z = MOTIF_THICKNESS - 0.40
DRIVE_LOCAL_END_Z = -RAINBOW_Z + PIVOT_POCKET_DEPTH
GUIDE_LOCAL_START_Z = MOTIF_THICKNESS - 0.40
GUIDE_LOCAL_END_Z = -LIGHTNING_Z + GUIDE_SLOT_DEPTH

# Cloud silhouette [assumed, sleepy lobe proportions].
CLOUD_BASE_W = 70.0
CLOUD_BASE_D = 31.0
CLOUD_BASE_CENTER_Y = -18.5
CLOUD_CENTER_R = 24.0
CLOUD_CENTER_Y = 7.0
CLOUD_LEFT_R = 19.0
CLOUD_LEFT_X = -25.0
CLOUD_LEFT_Y = -5.0
CLOUD_RIGHT_R = 18.0
CLOUD_RIGHT_X = 25.0
CLOUD_RIGHT_Y = -6.0
CLOUD_UPPER_LEFT_R = 13.0
CLOUD_UPPER_LEFT_X = -28.0
CLOUD_UPPER_LEFT_Y = 17.0

# Rainbow motif [assumed, then inverse-rotated into the closed pose].
RAINBOW_OUTER_R = 15.5
RAINBOW_BAND = 5.0
RAINBOW_CENTER_DEPLOYED = (25.0, -7.0)
RAINBOW_HUB_R = 8.5
RAINBOW_BRIDGE_W = 7.0
RAINBOW_ROOT_PAD_R = 4.2

# Lightning motif [assumed, broad rounded load path rather than a knife tip].
LIGHTNING_HUB_R = 8.0
LIGHTNING_BAR_W = 6.0
LIGHTNING_POINTS_DEPLOYED = ((0.0, -7.0), (-6.0, -16.0), (0.0, -17.0), (-9.0, -31.0))


def validate_parameters() -> None:
    assert CLOUD_THICKNESS >= 6.0
    assert MOTIF_THICKNESS >= 3.0
    assert DRIVE_SQUARE >= 5.0
    assert 0.09 <= (LIGHTNING_SOCKET - DRIVE_SQUARE) / 2.0 <= 0.12
    assert 0.15 <= (GUIDE_SLOT_W - GUIDE_PIN_D) / 2.0 <= 0.30
    assert PIVOT_BORE_D > math.sqrt(2.0) * DRIVE_SQUARE
    assert RAINBOW_BAND >= 4.0
    assert LIGHTNING_BAR_W >= 5.0
    assert DEPLOY_ANGLE_DEG == 90.0
    assert DRIVE_LOCAL_END_Z > DRIVE_LOCAL_START_Z
    assert GUIDE_LOCAL_END_Z > GUIDE_LOCAL_START_Z


validate_parameters()


def _bar_between(start: tuple[float, float], end: tuple[float, float], width: float, height: float):
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = math.hypot(dx, dy)
    angle = math.degrees(math.atan2(dy, dx))
    bar = Box(length, width, height, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return Pos((start[0] + end[0]) / 2.0, (start[1] + end[1]) / 2.0, 0.0) * Rot(0, 0, angle) * bar


def _closed_from_deployed(shape):
    return Rot(0, 0, -DEPLOY_ANGLE_DEG) * shape


def build_cloud():
    """Cloud receiver in assembly coordinates, face at Z=0 and back at +Z."""
    base = Pos(0, CLOUD_BASE_CENTER_Y, 0) * Box(
        CLOUD_BASE_W,
        CLOUD_BASE_D,
        CLOUD_THICKNESS,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    center = Pos(0, CLOUD_CENTER_Y, 0) * Cylinder(
        CLOUD_CENTER_R, CLOUD_THICKNESS, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    left = Pos(CLOUD_LEFT_X, CLOUD_LEFT_Y, 0) * Cylinder(
        CLOUD_LEFT_R, CLOUD_THICKNESS, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    right = Pos(CLOUD_RIGHT_X, CLOUD_RIGHT_Y, 0) * Cylinder(
        CLOUD_RIGHT_R, CLOUD_THICKNESS, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    upper_left = Pos(CLOUD_UPPER_LEFT_X, CLOUD_UPPER_LEFT_Y, 0) * Cylinder(
        CLOUD_UPPER_LEFT_R, CLOUD_THICKNESS, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    cloud = base.fuse(center, left, right, upper_left)

    # Blind pivot pocket: the square drive rotates inside this round receiver.
    pivot_pocket = Pos(PIVOT_X, PIVOT_Y, -0.10) * Cylinder(
        PIVOT_BORE_D / 2.0,
        PIVOT_POCKET_DEPTH + 0.10,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    # The guide pin follows a 90-degree blind arc. Its endcaps are the two hard stops.
    with BuildLine(Plane.XY) as guide_path:
        CenterArc((PIVOT_X, PIVOT_Y), GUIDE_RADIUS, 0.0, DEPLOY_ANGLE_DEG)
    with BuildSketch(Plane.XY) as guide_profile:
        SlotArc(guide_path.wire(), GUIDE_SLOT_W)
    guide_slot = extrude(guide_profile.sketch, amount=GUIDE_SLOT_DEPTH)

    # Sleepy face grooves open on the same side as the reveal pieces.
    left_eye = Pos(-12.0, 2.5, -0.10) * Rot(0, 0, -8.0) * Box(
        9.0, 1.8, 1.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    right_eye = Pos(12.0, 2.5, -0.10) * Rot(0, 0, 8.0) * Box(
        9.0, 1.8, 1.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    mouth = Pos(0, -7.0, -0.10) * Cylinder(
        1.8, 1.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )

    cloud = cloud.cut(pivot_pocket, guide_slot, left_eye, right_eye, mouth)
    cloud.label = "sleepy_cloud"
    assert len(cloud.solids()) == 1
    return cloud


def build_rainbow():
    """Outer rotor with an integral square drive, printed in its closed pose."""
    outer = Pos(*RAINBOW_CENTER_DEPLOYED, 0) * Cylinder(
        RAINBOW_OUTER_R,
        MOTIF_THICKNESS,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    inner = Pos(*RAINBOW_CENTER_DEPLOYED, -0.10) * Cylinder(
        RAINBOW_OUTER_R - RAINBOW_BAND,
        MOTIF_THICKNESS + 0.20,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    ring = outer.cut(inner)
    upper_clip = Pos(
        RAINBOW_CENTER_DEPLOYED[0],
        RAINBOW_CENTER_DEPLOYED[1] + RAINBOW_OUTER_R / 2.0,
        0,
    ) * Box(
        2.0 * RAINBOW_OUTER_R + 1.0,
        RAINBOW_OUTER_R + 1.0,
        MOTIF_THICKNESS,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    arch = ring & upper_clip
    cap_radius = RAINBOW_BAND / 2.0
    cap_offset = RAINBOW_OUTER_R - cap_radius
    left_cap = Pos(RAINBOW_CENTER_DEPLOYED[0] - cap_offset, RAINBOW_CENTER_DEPLOYED[1], 0) * Cylinder(
        cap_radius,
        MOTIF_THICKNESS,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    right_cap = Pos(RAINBOW_CENTER_DEPLOYED[0] + cap_offset, RAINBOW_CENTER_DEPLOYED[1], 0) * Cylinder(
        cap_radius,
        MOTIF_THICKNESS,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    arch = arch.fuse(left_cap, right_cap)
    hub = Cylinder(RAINBOW_HUB_R, MOTIF_THICKNESS, align=(Align.CENTER, Align.CENTER, Align.MIN))
    bridge_target = (RAINBOW_CENTER_DEPLOYED[0] - RAINBOW_OUTER_R + RAINBOW_BAND / 2.0, RAINBOW_CENTER_DEPLOYED[1] + RAINBOW_BAND / 2.0)
    bridge = _bar_between((0.0, 0.0), bridge_target, RAINBOW_BRIDGE_W, MOTIF_THICKNESS)
    root_pad = Pos(*bridge_target, 0) * Cylinder(
        RAINBOW_ROOT_PAD_R,
        MOTIF_THICKNESS,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    deployed_plate = hub.fuse(bridge, root_pad, arch)
    closed_plate = _closed_from_deployed(deployed_plate)

    drive_h = DRIVE_LOCAL_END_Z - DRIVE_LOCAL_START_Z
    drive = Pos(0, 0, DRIVE_LOCAL_START_Z) * Box(
        DRIVE_SQUARE,
        DRIVE_SQUARE,
        drive_h,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    rainbow = closed_plate.fuse(drive)
    rainbow.label = "rainbow_drive"
    assert len(rainbow.solids()) == 1
    return rainbow


def build_lightning():
    """Inner rotor with square socket and guide pin, printed in its closed pose."""
    deployed = Cylinder(LIGHTNING_HUB_R, MOTIF_THICKNESS, align=(Align.CENTER, Align.CENTER, Align.MIN))
    points = ((0.0, 0.0),) + LIGHTNING_POINTS_DEPLOYED
    for start, end in zip(points, points[1:]):
        deployed = deployed.fuse(_bar_between(start, end, LIGHTNING_BAR_W, MOTIF_THICKNESS))
        deployed = deployed.fuse(
            Pos(end[0], end[1], 0) * Cylinder(
                LIGHTNING_BAR_W / 2.0,
                MOTIF_THICKNESS,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
        )
    closed_plate = _closed_from_deployed(deployed)

    socket = Box(
        LIGHTNING_SOCKET,
        LIGHTNING_SOCKET,
        MOTIF_THICKNESS + 0.20,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    closed_plate = closed_plate.cut(Pos(0, 0, -0.10) * socket)

    # Broad root joins the off-axis guide pin to the rotor without a cantilever.
    guide_root = _bar_between((5.5, 0.0), (GUIDE_RADIUS, 0.0), 4.0, MOTIF_THICKNESS)
    closed_plate = closed_plate.fuse(guide_root)

    guide_h = GUIDE_LOCAL_END_Z - GUIDE_LOCAL_START_Z
    guide_pin = Pos(GUIDE_RADIUS, 0, GUIDE_LOCAL_START_Z) * Cylinder(
        GUIDE_PIN_D / 2.0,
        guide_h,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    lightning = closed_plate.fuse(guide_pin)
    lightning.label = "lightning_guide"
    assert len(lightning.solids()) == 1
    return lightning


def build_assembly(angle_deg: float = DEPLOY_ANGLE_DEG):
    """Labeled assembly at a source-controlled motion endpoint."""
    if not 0.0 <= angle_deg <= DEPLOY_ANGLE_DEG:
        raise ValueError("angle_deg must remain between the hard stops")
    cloud = build_cloud()
    cloud.label = "sleepy_cloud"

    rotor_transform = Pos(PIVOT_X, PIVOT_Y, 0) * Rot(0, 0, angle_deg)
    lightning = Pos(0, 0, LIGHTNING_Z) * rotor_transform * build_lightning()
    lightning.label = "lightning_guide"
    rainbow = Pos(0, 0, RAINBOW_Z) * rotor_transform * build_rainbow()
    rainbow.label = "rainbow_drive"

    reveal_rotor = Compound(label="reveal_rotor", children=[rainbow, lightning])
    reveal_rotor.label = "reveal_rotor"
    assembly = Compound(label="storm_reveal", children=[cloud, reveal_rotor])
    assembly.label = "storm_reveal"
    return assembly


def cloud_print_pose():
    # Flip the blind pockets upward while preserving a bed datum at Z=0.
    return Pos(0, 0, CLOUD_THICKNESS) * Rot(0, 180, 0) * build_cloud()
