"""Parametric geometry for Lunar Relay.

All dimensions are millimetres. Parts are authored in assembly coordinates;
the part entry files apply print-orientation transforms only.
"""

from __future__ import annotations

import math

try:
    # CAD launchers provide the canonical Workshop helper.
    import cadfits
except ModuleNotFoundError:
    # The host runs audits from an isolated copy with only the project on
    # PYTHONPATH. Keep that gate portable without guessing a workspace path.
    import cadfits_fallback as cadfits
from build123d import (
    Align,
    Box,
    BuildSketch,
    Cylinder,
    Plane,
    Polygon,
    Pos,
    Rot,
    extrude,
)
from cadgen import srgb
from cadgen.assembly import AssemblyHelper


# Manufacturing assumptions [assumed from Wish and 0.4 mm FDM baseline].
NOZZLE = 0.4
MIN_WALL = 2.0
MOVING_FIT = "free"

# Overall envelope and base [assumed].
BASE_W = 92.0
BASE_D = 54.0
BASE_T = 4.0
BASE_H = 25.0
PIVOT_Z = 17.5
CHEEK_X = 20.0
CHEEK_T = 5.0

# Lunar wells and rocker [assumed].
MOON_CENTER_X = 30.0
MOON_RADIUS = 11.0
GUARD_GAP = 2.0
GUARD_WALL = 3.0
GUARD_SPAN = 32.0
WELL_H = 4.0
ROCKER_LENGTH = 64.0
ROCKER_DEPTH = 14.0
ROCKER_T = 14.0
ROCKER_MAX_ANGLE_DEG = 8.0
CRATER_DEPTH = 1.4
ROCKER_SIDE_CLEARANCE = 0.50
CHEEK_INNER_GAP = cadfits.slot_for(ROCKER_DEPTH, ROCKER_SIDE_CLEARANCE)
CHEEK_CENTER_Y = (CHEEK_INNER_GAP + CHEEK_T) / 2.0

# The male axle owns the mating dimension; all openings derive from it.
AXLE_D = 6.0
BORE_ACROSS_FLATS = cadfits.slot_for(AXLE_D, MOVING_FIT)
DIAMOND_DIAGONAL = BORE_ACROSS_FLATS * math.sqrt(2.0)
KEY_TAB_W = 13.0
KEY_TAB_T = 3.2
KEYWAY_W = cadfits.slot_for(KEY_TAB_W, MOVING_FIT)
KEYWAY_H = cadfits.slot_for(KEY_TAB_T, MOVING_FIT)

# Axle geometry [assumed]. +Y is the headed side; -Y is the locking-tab side.
AXLE_SHAFT_Y_MIN = -13.5
AXLE_SHAFT_Y_MAX = 14.0
AXLE_SHAFT_LENGTH = AXLE_SHAFT_Y_MAX - AXLE_SHAFT_Y_MIN
AXLE_SHAFT_CENTER_Y = (AXLE_SHAFT_Y_MIN + AXLE_SHAFT_Y_MAX) / 2.0
HEAD_RADIUS = 6.5
HEAD_T = 3.0
HEAD_CENTER_Y = 15.5
TAB_NECK_Y = -13.5
TAB_FULL_Y = -17.5
TAB_END_Y = -18.7


def validate_parameters() -> None:
    """Cheap algebraic design-intent checks before any B-rep work."""

    assert BASE_W <= 120.0 and BASE_D <= 120.0 and BASE_H <= 120.0
    assert BASE_T >= 5 * NOZZLE
    assert GUARD_WALL >= MIN_WALL
    assert math.isclose(
        CHEEK_INNER_GAP,
        cadfits.slot_for(ROCKER_DEPTH, ROCKER_SIDE_CLEARANCE),
    )
    assert math.isclose(BORE_ACROSS_FLATS, cadfits.slot_for(AXLE_D, MOVING_FIT))
    assert math.isclose(KEYWAY_W, cadfits.slot_for(KEY_TAB_W, MOVING_FIT))
    assert math.isclose(KEYWAY_H, cadfits.slot_for(KEY_TAB_T, MOVING_FIT))
    assert KEYWAY_W > KEY_TAB_W and KEYWAY_H > KEY_TAB_T
    # In the locked pose the wide tab is vertical and cannot pass the diamond.
    assert KEY_TAB_W > DIAMOND_DIAGONAL + 2.0
    # The first print overhang expands 3.5 mm over 4 mm: steeper than 45 degrees.
    assert (KEY_TAB_W / 2.0 - AXLE_D / 2.0) <= abs(TAB_FULL_Y - TAB_NECK_Y)
    # Declared motion clears the floor; the floor becomes a hard stop later.
    travel = MOON_CENTER_X * math.sin(math.radians(ROCKER_MAX_ANGLE_DEG))
    assert PIVOT_Z - ROCKER_T / 2.0 - travel > BASE_T


validate_parameters()


def _centered_box(x: float, y: float, z: float):
    return Box(x, y, z, align=(Align.CENTER, Align.CENTER, Align.CENTER))


def _pivot_opening(cut_depth: float):
    """Support-free diamond bearing plus unlocked horizontal keyway."""

    diamond = Rot(0, 45, 0) * _centered_box(
        BORE_ACROSS_FLATS, cut_depth, BORE_ACROSS_FLATS
    )
    keyway = _centered_box(KEYWAY_W, cut_depth, KEYWAY_H)
    return Pos(0, 0, PIVOT_Z) * (diamond + keyway)


def make_lunar_base(*, with_color: bool = True):
    floor = Box(
        BASE_W,
        BASE_D,
        BASE_T,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    cheeks = []
    for y in (-CHEEK_CENTER_Y, CHEEK_CENTER_Y):
        cheek = Pos(0, y, BASE_T) * Box(
            CHEEK_X,
            CHEEK_T,
            BASE_H - BASE_T,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        cheeks.append(cheek)

    guards = []
    for x in (-MOON_CENTER_X, MOON_CENTER_X):
        side_y = MOON_RADIUS + GUARD_GAP + GUARD_WALL / 2.0
        for y in (-side_y, side_y):
            guards.append(
                Pos(x, y, BASE_T)
                * Box(
                    GUARD_SPAN,
                    GUARD_WALL,
                    WELL_H,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                )
            )
        outward = -1.0 if x < 0 else 1.0
        outer_x = x + outward * (MOON_RADIUS + GUARD_GAP + GUARD_WALL / 2.0)
        guards.append(
            Pos(outer_x, 0, BASE_T)
            * Box(
                GUARD_WALL,
                GUARD_SPAN,
                WELL_H,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
        )

    base = floor + cheeks + guards
    base = base - _pivot_opening(BASE_D + 2.0)
    base.label = "lunar_base"
    if with_color:
        base.color = srgb("#222A38")
    assert len(base.solids()) == 1
    return base


def _crater_cutters():
    cutters = []
    patterns = (
        ((-3.7, -2.4, 2.0), (2.8, 3.0, 1.6), (3.8, -3.4, 1.25)),
        ((-3.0, 3.4, 1.7), (3.4, -2.0, 2.0), (1.0, 3.8, 1.15)),
    )
    for moon_x, pattern in zip((-MOON_CENTER_X, MOON_CENTER_X), patterns):
        for dx, dy, radius in pattern:
            cutters.append(
                Pos(moon_x + dx, dy, ROCKER_T / 2.0 - CRATER_DEPTH)
                * Cylinder(
                    radius,
                    CRATER_DEPTH + 0.5,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                )
            )
    return cutters


def make_moon_rocker(*, with_color: bool = True):
    bar = _centered_box(ROCKER_LENGTH, ROCKER_DEPTH, ROCKER_T)
    moons = [
        Pos(x, 0, 0)
        * Cylinder(
            MOON_RADIUS,
            ROCKER_T,
            align=(Align.CENTER, Align.CENTER, Align.CENTER),
        )
        for x in (-MOON_CENTER_X, MOON_CENTER_X)
    ]
    rocker = bar + moons
    rocker = rocker - Pos(0, 0, -PIVOT_Z) * _pivot_opening(ROCKER_DEPTH + 2.0)
    rocker = rocker - _crater_cutters()
    rocker.label = "moon_rocker"
    if with_color:
        rocker.color = srgb("#D8DEE9")
    assert len(rocker.solids()) == 1
    return rocker


def _locked_tab():
    """Tab with 41 degree printable shoulders when the axle stands on its head."""

    profile = (
        (TAB_NECK_Y, -AXLE_D / 2.0),
        (TAB_NECK_Y, AXLE_D / 2.0),
        (TAB_FULL_Y, KEY_TAB_W / 2.0),
        (TAB_END_Y, KEY_TAB_W / 2.0),
        (TAB_END_Y, -KEY_TAB_W / 2.0),
        (TAB_FULL_Y, -KEY_TAB_W / 2.0),
    )
    with BuildSketch(Plane.YZ) as tab_sketch:
        Polygon(*profile)
    return extrude(tab_sketch.sketch, KEY_TAB_T / 2.0, both=True)


def make_quarter_turn_axle(*, with_color: bool = True):
    shaft = Pos(0, AXLE_SHAFT_CENTER_Y, 0) * Rot(90, 0, 0) * Cylinder(
        AXLE_D / 2.0,
        AXLE_SHAFT_LENGTH,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    head = Pos(0, HEAD_CENTER_Y, 0) * Rot(90, 0, 0) * Cylinder(
        HEAD_RADIUS,
        HEAD_T,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    axle = shaft + head + _locked_tab()
    axle.label = "quarter_turn_axle"
    if with_color:
        axle.color = srgb("#D89B3C")
    assert len(axle.solids()) == 1
    return axle


def make_assembly():
    asm = AssemblyHelper("lunar_relay")
    # Open CASCADE serializes multiple per-child assembly styles through an
    # unordered internal map, so otherwise identical fresh processes can swap
    # style records and change the STEP bytes. Keep the declared assembly STEP
    # unstyled and deterministic; printable part entries retain their colors.
    asm.add(make_lunar_base(with_color=False), "lunar_base")
    asm.add(
        Pos(0, 0, PIVOT_Z) * make_moon_rocker(with_color=False),
        "moon_rocker",
    )
    asm.add(
        Pos(0, 0, PIVOT_Z) * make_quarter_turn_axle(with_color=False),
        "quarter_turn_axle",
    )
    return asm.build()


def print_pose_base():
    return make_lunar_base()


def print_pose_rocker():
    return Pos(0, 0, ROCKER_T / 2.0) * make_moon_rocker()


def print_pose_axle():
    rotated = Rot(-90, 0, 0) * make_quarter_turn_axle()
    return Pos(0, 0, -rotated.bounding_box().min.Z) * rotated
