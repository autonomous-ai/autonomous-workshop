"""Shared parametric geometry for the three-part Moon-Moth Bloom."""

from __future__ import annotations

import math

import cadfits
from build123d import Align, Circle, Compound, Cylinder, Ellipse, Polygon, Pos, Rot, extrude, fillet


# Assembly and print parameters, millimetres/degrees.
PIVOT_X = 9.0
PIVOT_Y = -7.5
BASE_RX = 27.0
BASE_RY = 39.0
BASE_T = 2.4
SHELF_TOP = 4.5
WING_T = 3.0
SEATED_Z = 4.5
RAISED_Z = 5.7
DROP_Q = 78.0
OPEN_Q = 82.0
SERVICE_Q = 118.0
POST_D = 5.0
FLANGE_D = 7.4
JOURNAL_RUNNING_CLEARANCE = 0.30
KEYHOLE_LOBE_CLEARANCE = "slip"
KEYHOLE_THROAT_CLEARANCE = 0.50
BORE_D = cadfits.slot_for(POST_D, JOURNAL_RUNNING_CLEARANCE)
LOBE_D = cadfits.slot_for(FLANGE_D, KEYHOLE_LOBE_CLEARANCE)
THROAT_W = cadfits.slot_for(POST_D, KEYHOLE_THROAT_CLEARANCE)
LOW_UNDERSIDE = 8.0
LOW_TOP = 10.4
HIGH_UNDERSIDE = 9.2
HIGH_TOP = 10.8
MODULE = 1.0
TEETH = 18
PRESSURE_ANGLE_DEG = 20.0
PITCH_R = MODULE * TEETH / 2.0
ROOT_R = PITCH_R - 1.25 * MODULE
OUTER_R = PITCH_R + MODULE
PAIR_BACKLASH = 0.40
NECK_W = 0.90
CHANNEL_INNER = 16.0
CHANNEL_OUTER = 18.0
CHANNEL_WALL = 0.8
LOW_Q_INNER_END = 64.0
LOW_Q_END_EDGE = 68.0
HIGH_Q_START = 79.5
HIGH_Q_END = 118.0
CYLINDER_BASE = (Align.CENTER, Align.CENTER, Align.MIN)

# Stable interface names and the physically ordered service path are shared
# with measure/check_fit.py.  These are evidence identifiers, not geometry.
CONNECTOR_NAMES = (
    "left-journal-post-to-running-bore",
    "right-journal-post-to-running-bore",
    "left-mushroom-flange-to-keyhole-lobe",
    "right-mushroom-flange-to-keyhole-lobe",
    "module-1-eighteen-tooth-external-gear-pair",
)
ASSEMBLY_SEQUENCE = (
    "load-keyhole-lobes-over-flanges-at-q118",
    "seat-both-wings-raised-at-z5.7",
    "counter-rotate-under-high-hood-to-q82",
    "drop-both-wings-1.2mm-at-q78",
    "continue-seated-beneath-low-roof",
)


def _polar(radius: float, angle_deg: float) -> tuple[float, float]:
    a = math.radians(angle_deg)
    return radius * math.cos(a), radius * math.sin(a)


def _sector(r0: float, r1: float, a0: float, a1: float):
    """CCW annular-sector face with stable polygonal edges."""
    steps = max(3, int(abs(a1 - a0) / 4.0) + 1)
    angles = [a0 + (a1 - a0) * i / steps for i in range(steps + 1)]
    points = [_polar(r1, a) for a in angles]
    points += [_polar(r0, a) for a in reversed(angles)]
    return Polygon(*points)


def _tapered_sector(
    r0: float,
    r1: float,
    outer_a0: float,
    outer_a1: float,
    inner_a0: float,
    inner_a1: float,
):
    """Annular sector whose radial end is angled to open a drop window."""
    steps = max(3, int(abs(outer_a1 - outer_a0) / 4.0) + 1)
    outer = [outer_a0 + (outer_a1 - outer_a0) * i / steps for i in range(steps + 1)]
    inner = [inner_a0 + (inner_a1 - inner_a0) * i / steps for i in range(steps + 1)]
    points = [_polar(r1, a) for a in outer]
    points += [_polar(r0, a) for a in reversed(inner)]
    return Polygon(*points)


def _radial_bar(r0: float, r1: float, angle_deg: float, width: float = 2.0):
    """CCW rectangular end bar that removes knife-like sector terminations."""
    angle = math.radians(angle_deg)
    ux, uy = math.cos(angle), math.sin(angle)
    vx, vy = -uy, ux
    h = width / 2.0
    points = [
        (ux * r0 - vx * h, uy * r0 - vy * h),
        (ux * r1 - vx * h, uy * r1 - vy * h),
        (ux * r1 + vx * h, uy * r1 + vy * h),
        (ux * r0 + vx * h, uy * r0 + vy * h),
    ]
    return Polygon(*points)


def _gear_face(phase_deg: float = 0.0):
    """One complete rounded 18T printable gear face on the module-1 pitch."""
    pitch = 2.0 * math.pi / TEETH
    tooth_radius = 0.95
    tooth_centre_radius = PITCH_R - 0.75
    teeth = []
    for tooth in range(TEETH):
        angle = phase_deg + math.degrees(tooth * pitch)
        x, y = _polar(tooth_centre_radius, angle)
        teeth.append(Pos(x, y) * Circle(tooth_radius))
    return Circle(ROOT_R) + teeth


def _star_face(cx: float, cy: float, outer: float, inner: float):
    points = []
    for i in range(10):
        radius = outer if i % 2 == 0 else inner
        angle = 90.0 + i * 36.0
        x, y = _polar(radius, angle)
        points.append((cx + x, cy + y))
    return Polygon(*reversed(points))


def _channel_solids(pivot_x: float, side: int, high: bool):
    """Post-supported canopy with a distal low operating lip."""
    if side < 0:  # left: +q from local +Y
        if high:
            a0, a1 = 90.0 + HIGH_Q_START, 90.0 + HIGH_Q_END
        else:
            a0, a1 = 88.0, 90.0 + LOW_Q_END_EDGE
    else:  # right: -q from local +Y
        if high:
            a0, a1 = 90.0 - HIGH_Q_END, 90.0 - HIGH_Q_START
        else:
            a0, a1 = 90.0 - LOW_Q_END_EDGE, 92.0
    canopy_profile = _sector(POST_D / 2.0 - 0.1, CHANNEL_OUTER, a0, a1) + [
        _radial_bar(POST_D / 2.0 - 0.2, CHANNEL_OUTER, a0),
        _radial_bar(POST_D / 2.0 - 0.2, CHANNEL_OUTER, a1),
    ]
    canopy = Pos(pivot_x, PIVOT_Y, HIGH_UNDERSIDE) * extrude(
        canopy_profile,
        amount=HIGH_TOP - HIGH_UNDERSIDE,
    )
    if high:
        return [canopy]
    if side < 0:
        low_profile = _tapered_sector(
            CHANNEL_INNER, CHANNEL_OUTER, a0, a1, a0, 90.0 + LOW_Q_INNER_END
        )
        low_end_angle = 90.0 + (LOW_Q_INNER_END + LOW_Q_END_EDGE) / 2.0
    else:
        low_profile = _tapered_sector(
            CHANNEL_INNER, CHANNEL_OUTER, a0, a1, 90.0 - LOW_Q_INNER_END, a1
        )
        low_end_angle = 90.0 - (LOW_Q_INNER_END + LOW_Q_END_EDGE) / 2.0
    low_profile = low_profile + [
        _radial_bar(CHANNEL_INNER, CHANNEL_OUTER, low_end_angle),
    ]
    low_lip = Pos(pivot_x, PIVOT_Y, LOW_UNDERSIDE) * extrude(
        low_profile,
        amount=LOW_TOP - LOW_UNDERSIDE,
    )
    return [canopy, low_lip]


def _canopy_solids(pivot_x: float, side: int):
    """Discrete low capture buttons on the seated arc."""
    buttons = []
    for q in (20.0, 41.0, 62.0, 68.0):
        angle = 90.0 + q if side < 0 else 90.0 - q
        dx, dy = _polar(16.8, angle)
        buttons.append(
            Pos(pivot_x + dx, PIVOT_Y + dy, LOW_UNDERSIDE)
            * Cylinder(1.2, LOW_TOP - LOW_UNDERSIDE, align=CYLINDER_BASE)
        )
    return buttons


def make_chassis():
    floor = extrude(Ellipse(BASE_RX, BASE_RY), amount=BASE_T)
    shelves = []
    posts = []
    for x in (-PIVOT_X, PIVOT_X):
        shelves.append(Pos(x, PIVOT_Y, BASE_T) * Cylinder(PITCH_R + 1.6, SHELF_TOP - BASE_T, align=CYLINDER_BASE))
        posts.append(Pos(x, PIVOT_Y, BASE_T) * Cylinder(POST_D / 2.0, HIGH_UNDERSIDE - BASE_T + 0.1, align=CYLINDER_BASE))
    canopy_local = extrude(
        Ellipse(BASE_RX, CHANNEL_OUTER), amount=HIGH_TOP - HIGH_UNDERSIDE
    )
    canopy_local = fillet(canopy_local.edges(), radius=0.3)
    canopy = Pos(0, PIVOT_Y, HIGH_UNDERSIDE) * canopy_local
    channels = [canopy]
    channels += _canopy_solids(-PIVOT_X, -1)
    channels += _canopy_solids(PIVOT_X, 1)
    body = floor + [*shelves, *posts, *channels]
    body.label = "chassis"
    return body


def _wing_outline(side: int):
    shift = 2.0 * float(side)
    points = [
        (3.0, 7.0),
        (NECK_W / 2.0, 20.5),
        (8.5 + shift, 28.0),
        (10.5 + shift, 35.5),
        (6.0 + shift, 42.5),
        (shift, 46.5),
        (-6.0 + shift, 42.5),
        (-10.5 + shift, 35.5),
        (-8.5 + shift, 28.0),
        (-NECK_W / 2.0, 20.5),
        (-3.0, 7.0),
    ]
    return Polygon(*points)


def make_wing(side: int):
    """Build one bed-pose wing; side=-1 left, +1 right."""
    phase = 0.0 if side < 0 else 180.0 / TEETH
    profile = _gear_face(phase) + [_wing_outline(side)]
    body = extrude(profile, amount=WING_T)

    lobe_y = -2.8
    bore = Pos(0, 0, -1.0) * Cylinder(BORE_D / 2.0, WING_T + 2.0, align=CYLINDER_BASE)
    lobe = Pos(0, lobe_y, -1.0) * Cylinder(LOBE_D / 2.0, WING_T + 2.0, align=CYLINDER_BASE)
    throat = Pos(-THROAT_W / 2.0, lobe_y, -1.0) * extrude(
        Polygon((0, 0), (THROAT_W, 0), (THROAT_W, -lobe_y), (0, -lobe_y)),
        amount=WING_T + 2.0,
    )
    star_x = 1.2 * side
    star_tools = [
        Pos(0, 0, -1.0) * extrude(_star_face(star_x - 2.0 * side, 29.0, 2.4, 1.05), amount=5.0),
        Pos(0, 0, -1.0) * extrude(_star_face(star_x + 2.4 * side, 35.5, 2.2, 0.95), amount=5.0),
        Pos(0, 0, -1.0) * extrude(_star_face(star_x - 1.2 * side, 41.0, 1.8, 0.8), amount=5.0),
    ]
    body = body - [bore, lobe, throat, *star_tools]
    body.label = "left_wing_control" if side < 0 else "right_wing"
    return body


def placed_wing(side: int, q_deg: float, z: float = SEATED_Z, explode: float = 0.0):
    wing = make_wing(side)
    x = side * PIVOT_X + side * explode
    rotation = q_deg if side < 0 else -q_deg
    return Pos(x, PIVOT_Y, z) * Rot(0, 0, rotation) * wing


def make_assembly(q_deg: float = 41.0, z: float = SEATED_Z, explode: float = 0.0):
    chassis = make_chassis()
    left = placed_wing(-1, q_deg, z, explode)
    right = placed_wing(1, q_deg, z, explode)
    chassis.label = "chassis"
    left.label = "left_wing_control"
    right.label = "right_wing"
    assembly = Compound(children=[chassis, left, right])
    assembly.label = "moon_moth_bloom"
    return assembly
