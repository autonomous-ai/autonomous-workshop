"""CLEARANCE (g0003) — every dimension and every part builder.

All numbers come from games/g0003/brief.md. Where a built value differs from a
brief value the reason is in cad/DEVIATIONS.md and marked [DEV] here.

Frames
------
ASSEMBLY frame: Z = 0 is the runway (the gantry base's top face), which is the
datum every bar height is measured from. X runs along the lane; the screw axis
is at x = -95, the guide-post axis at x = +95. The setter sits at -Y.

Each part builder returns the part in the ASSEMBLY frame at the nominal render
position; the `part_*.step.py` entries move it to its print orientation with
min(Z) = 0.
"""

from __future__ import annotations

import math

from build123d import (
    Align,
    Axis,
    Box,
    Cone,
    Cylinder,
    Location,
    Plane,
    Pos,
    Rot,
    Sphere,
    Text,
    chamfer,
    extrude,
    fillet,
)

import cadfits
import threads

# --------------------------------------------------------------------------
# 1. Datum stack (brief §1) — all Z from the runway
# --------------------------------------------------------------------------
RUNWAY_Z = 0.0
SHROUD_TOP_Z = 24.0
KNOB_UNDER_Z = 76.0
KNOB_TOP_Z = 90.0
H_TOP_NOM = 33.00          # nominal bar height at the hard top stop; measured per copy (§5.1)
TRAVEL = 15.50             # 31 clicks x 0.500
CLICK = 0.500
H_BOTTOM_NOM = H_TOP_NOM - TRAVEL

SCREW_X = -95.0
POST_X = +95.0
AXIS_SPAN = POST_X - SCREW_X   # 190.0 (§3.9)

# --------------------------------------------------------------------------
# 2. Thread pair — one nominal, one clearance, both halves derived
# --------------------------------------------------------------------------
THREAD_PITCH = 2.00
THREAD_MAJOR = 16.00           # screw major, +0.00/-0.15
THREAD_Z0 = 24.0               # thread starts here (§7.5)
THREAD_Z1 = 66.0               # ...and ends here
THREAD_LEN = THREAD_Z1 - THREAD_Z0
NUT_FLANK_CLEARANCE = 0.35     # total diametral, running fit
NUT_MAJOR = 16.70              # nut bore (+0.15/-0.00)
NUT_LEN = 20.0

# --------------------------------------------------------------------------
# 3. Gantry base
# --------------------------------------------------------------------------
BASE_L = 220.0
BASE_D = 78.0
BASE_T = 10.0
BASE_SKIN = 3.0                # runway skin over the ribbed underside
FOOT_D = 16.0
FOOT_H = 3.5
LANE_HALF = 65.1               # lane clear half-width; 130.2 = 130.0 +0.5/-0.0

COLLAR_D = 24.0                # [DEV] detent crown and journal collar are ONE collar
COLLAR_H = 8.0
COLLAR_Z0 = -9.0               # collar bottom rests on the journal floor
COLLAR_Z1 = COLLAR_Z0 + COLLAR_H
JOURNAL_D = COLLAR_D + 0.40    # running clearance 0.40 diametral (brief fit class)
JOURNAL_DEPTH = 9.0            # below the runway
SHROUD_OD = 28.0               # [DEV] 24.0 -> 28.0; the D24 collar must pass the bore
NOTCH_COUNT = 4
NOTCH_DEPTH = 0.80
NOTCH_RAMP_DEG = 30.0          # flank angle to the direction of travel (§3.5)

POST_D = 12.00
POST_LEN = 82.0
POST_SOCKET_D = 11.90          # 0.10 interference -> transition/light press
POST_SOCKET_DEPTH = 10.0
POST_BOTTOM_Z = -BASE_T
POST_TOP_Z = POST_BOTTOM_Z + POST_LEN      # +72.0 — the hard top stop

LEAF_L = 34.0
LEAF_H = 12.0                  # the spring's width b; vertical when installed
LEAF_ROOT_T = 4.0
LEAF_SPRING_T = 1.60           # the tuning dimension (§3.5)
LEAF_FREE_L = 24.0
LEAF_ROOT_L = LEAF_L - LEAF_FREE_L
LEAF_SOCKET_T = 4.30
LEAF_RIB = 0.10                # per side -> 0.10 total interference, a snap
NUB_D = 3.0
LEAF_TOP_Z = -0.30             # just under the runway, so the stop ring never touches it
LEAF_BOT_Z = LEAF_TOP_Z - LEAF_H
LEAF_FACE_R = COLLAR_D / 2 - NOTCH_DEPTH + NUB_D / 2   # 12.7: nub tip seats at r=11.2
LEAF_X = SCREW_X + LEAF_FACE_R
NUB_Z = LEAF_TOP_Z - LEAF_H / 2                        # -6.3, mid-collar

RITUAL_LINES = ("DOWN 5 UP 3", "DOWN 6 UP 2", "DOWN 7 UP 1")

# --------------------------------------------------------------------------
# 4. Yoke — local Z is measured from H_bar (the bar's lowest point)
# --------------------------------------------------------------------------
YOKE_HALF_L = 112.0
YOKE_HALF_D = 17.0
SADDLE_X = 72.0
SADDLE_DEPTH = 4.0
SADDLE_APEX_Z = -1.657         # bar r/sin45 = 5.657 above the apex (§3.6)
SADDLE_RIM_Z = SADDLE_APEX_Z + SADDLE_DEPTH
SADDLE_RELIEF_D = 2.0
BAR_D = 8.0
BAR_LEN = 158.0
BAR_AXIS_Z = 4.0
BRIDGE_UNDER_Z = 11.0
BRIDGE_TOP_Z = 17.0
BRIDGE_HALF_D = 12.0
SKIRT_ID = 30.0
SKIRT_OD = 34.0
SKIRT_RIM_Z = -15.0            # = H_bar - 15; 18.0 at H_top, 2.5 at H_bottom (§3.10)
BOSS_REF_Z = SKIRT_RIM_Z + 21.0   # +6.0
CAVITY_TOP_Z = 8.0             # clears the shroud top at H_bottom by 1.5
NUT_Z0 = 14.65                 # local; cone from D30 to D16.7 at 45 deg lands here
NUT_Z1 = NUT_Z0 + NUT_LEN
POST_BORE_D = 12.40            # running clearance 0.40 diametral
POST_BORE_DEPTH = 54.0
POST_BORE_TOP_Z = SKIRT_RIM_Z + POST_BORE_DEPTH   # +39 -> 72.0 at H_top = post top
TOWER_TOP_Z = POST_BORE_TOP_Z + 2.0               # +41
TOWER_FLARE_D = 48.0
PEDESTAL_BOT_Z = -5.0

# --------------------------------------------------------------------------
# 5. Stop ring, hood, rails, blocks
# --------------------------------------------------------------------------
RING_OD = 36.0
RING_ID = SHROUD_OD + 0.6
RING_H = 2.35                  # per copy (§5.3): skirt-rim Z at top stop - 15.50 - 0.15

HOOD_OD = 82.0
HOOD_WALL = 1.6
HOOD_RIM_Z = 52.0              # [DEV] 6.0 -> 52.0; below this the shell strikes the yoke
HOOD_CEIL_Z = KNOB_TOP_Z       # the ledge rests on the knob top face
HOOD_TOP_Z = HOOD_CEIL_Z + HOOD_WALL
HOOD_LEDGE_D = 44.40           # +0.20/-0.00 over the D44 knob
HOOD_LEDGE_DEPTH = 10.0
HOOD_TAB_W = 26.0

KNOB_D = 44.0
KNOB_H = KNOB_TOP_Z - KNOB_UNDER_Z

RAIL_L = 178.0
RAIL_D = 32.0
RAIL_T = 8.0
POCKET = 21.0
POCKET_DEPTH = 3.0
POCKET_PITCH = 28.0
POCKET_N = 6

PIECE = 20.0
PIECE_CHAMFER = 0.4
PIP_D = 2.0
PIP_DEPTH = 0.5
PIP_PITCH = 4.0

BED = 251.0

SET_KEYS = ("a", "b", "c", "d", "e")


# --------------------------------------------------------------------------
# Parameter checks — algebraic, run before any geometry
# --------------------------------------------------------------------------
def _check_params() -> None:
    assert abs(TRAVEL / CLICK - 31) < 1e-9, "31 clicks x 0.5 mm = 15.50 mm"
    assert abs(CLICK - THREAD_PITCH / NOTCH_COUNT) < 1e-9, "one quarter turn = one click"
    assert JOURNAL_D - COLLAR_D == 0.40, "collar/journal running fit"
    assert POST_D - POST_SOCKET_D == 0.10, "post press fit into the base"
    assert POST_BORE_D - POST_D == 0.40, "post/yoke running fit"
    assert SHROUD_OD + 1.0 <= SKIRT_ID, "shroud must telescope inside the yoke skirt"
    assert JOURNAL_D + 0.2 <= SHROUD_OD - 2 * 1.6, "the collar must pass the shroud bore"
    assert RING_OD > SKIRT_OD, "the skirt rim has to land on the ring"
    assert RING_ID > SHROUD_OD, "the ring drops over the shroud"
    assert abs((H_TOP_NOM + 15.0) - (SKIRT_RIM_Z + H_TOP_NOM + 15.0)) < 1e-9
    assert abs(POST_TOP_Z - (H_TOP_NOM + POST_BORE_TOP_Z)) < 1e-9, (
        "the post top IS the hard top stop: H_top = post_top - 39"
    )
    assert H_BOTTOM_NOM + SKIRT_RIM_Z < RING_H + 0.2, "the ring must stop travel at 31 clicks"
    assert SADDLE_X + 8 < YOKE_HALF_L, "saddles sit inside the end blocks"
    assert BAR_LEN > 2 * SADDLE_X, "the bar spans both saddles"
    assert 2 * YOKE_HALF_L <= BED and BASE_L <= BED
    assert LANE_HALF * 2 >= 130.0 and LANE_HALF * 2 <= 130.5, "lane 130 +0.5/-0.0"
    assert cadfits.slot_for(LEAF_ROOT_T + 2 * LEAF_RIB, -0.05) == LEAF_SOCKET_T, (
        "leaf snap: ribbed root 4.40 in a 4.30 socket = 0.10 interference"
    )
    # the yoke nut has to stay on the thread over the whole travel
    assert H_BOTTOM_NOM + NUT_Z0 >= THREAD_Z0 - 0.01, "nut runs off the thread at the bottom"
    assert H_TOP_NOM + NUT_Z0 + 12 <= THREAD_Z1, "not enough engagement at the top"


_check_params()


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def _cyl(d: float, h: float, z: float = 0.0, x: float = 0.0, y: float = 0.0):
    return Pos(x, y, z) * Cylinder(
        d / 2, h, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )


def _tube(od: float, idia: float, h: float, z: float, x: float = 0.0):
    return _cyl(od, h, z, x) - _cyl(idia, h + 2, z - 1, x)


def _bore_lead_in(d: float, z: float, x: float = 0.0, up: bool = True, size: float = 1.5):
    """1.5 x 30 deg lead-in cone to cut from a bore mouth (§6 step 4)."""
    r = d / 2
    grow = size * math.tan(math.radians(30.0)) + 0.4
    if up:
        return Pos(x, 0, z - size) * Cone(
            r, r + grow, size, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
    return Pos(x, 0, z) * Cone(
        r + grow, r, size, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )


def _end_chamfer(d: float, z: float, x: float = 0.0, top: bool = True, size: float = 1.0):
    """Cut this from a male end to chamfer it (a selector-free chamfer)."""
    r = d / 2
    ring = _cyl(d + 4, size + 0.2, z - (size if top else 0.0) - 0.1, x)
    if top:
        cone = Pos(x, 0, z - size - 0.1) * Cone(
            r, r - size, size + 0.2, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
    else:
        cone = Pos(x, 0, z - 0.1) * Cone(
            r - size, r, size + 0.2, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
    return ring - cone


def screw_bore_cut(top_z: float):
    """The base's screw bore: journal, then a plain bore up through the shroud."""
    return _cyl(JOURNAL_D, top_z - COLLAR_Z0 + 1, COLLAR_Z0, SCREW_X)


def leaf_pocket_cut():
    """Leaf socket, its nub window into the journal, and the flex clearance."""
    slot = Pos(LEAF_X + LEAF_SOCKET_T / 2 - 0.05, -(LEAF_L + 0.2) / 2 + 0.1, LEAF_BOT_Z) * Box(
        LEAF_SOCKET_T, LEAF_L + 0.2, LEAF_H + 1, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    window = Pos(SCREW_X + 10.0, 0, COLLAR_Z0 - 0.5) * Box(
        8.0, NUB_D + 1.5, COLLAR_H + 1, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    return slot + window


# --------------------------------------------------------------------------
# gantry_base
# --------------------------------------------------------------------------
def build_gantry_base():
    plate = Pos(0, 0, -BASE_T) * Box(
        BASE_L, BASE_D, BASE_T, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    plate = chamfer(plate.edges().filter_by(Axis.Z), 2.0)

    shroud = _tube(SHROUD_OD, JOURNAL_D, SHROUD_TOP_Z, 0.0, SCREW_X)
    part = plate + shroud

    # ribbed underside: 7 mm deep pockets, 3 mm runway skin, 3 mm ribs
    pockets = None
    rib = 3.0
    cell = 27.0
    nx = int((BASE_L - 2 * 8) // (cell + rib))
    ny = int((BASE_D - 2 * 8) // (cell + rib))
    x0 = -((nx - 1) * (cell + rib)) / 2
    y0 = -((ny - 1) * (cell + rib)) / 2
    for i in range(nx):
        for j in range(ny):
            cx = x0 + i * (cell + rib)
            cy = y0 + j * (cell + rib)
            if math.hypot(cx - SCREW_X, cy) < 30 or math.hypot(cx - POST_X, cy) < 22:
                continue
            if abs(cx - LEAF_X) < 22 and -40 < cy < 6:
                continue
            p = Pos(cx, cy, -BASE_T) * Box(
                cell, cell, BASE_T - BASE_SKIN, align=(Align.CENTER, Align.CENTER, Align.MIN)
            )
            pockets = p if pockets is None else pockets + p
    part = part - pockets

    # local pad so the 12 mm leaf socket has a floor inside a 10 mm plate
    pad = Pos(LEAF_X + 0.5, -17.0, LEAF_BOT_Z - 0.5) * Box(
        LEAF_SOCKET_T + 6, LEAF_L + 4, (-BASE_T) - (LEAF_BOT_Z - 0.5),
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    part = part + pad

    for fx, fy in ((-100.0, -30.0), (100.0, -30.0), (0.0, 30.0)):
        part = part + _cyl(FOOT_D, FOOT_H, -BASE_T - FOOT_H, fx, fy)

    part = part - screw_bore_cut(SHROUD_TOP_Z)
    part = part - leaf_pocket_cut()
    part = part - _cyl(POST_SOCKET_D, POST_SOCKET_DEPTH + 1, -BASE_T - 0.5, POST_X)

    # lead-in chamfers (§6 step 4): two blind alignments have to be made at once
    part = part - _bore_lead_in(JOURNAL_D, SHROUD_TOP_Z, SCREW_X)
    part = part - _bore_lead_in(POST_SOCKET_D, RUNWAY_Z, POST_X)

    # the setter's ritual, embossed on the front skirt (§7.6)
    for k, line in enumerate(RITUAL_LINES):
        sk = Plane.XZ.offset(BASE_D / 2) * Pos(0, -3.0 - 2.8 * k) * Text(
            line, font_size=2.2, align=(Align.CENTER, Align.CENTER)
        )
        part = part + extrude(sk, amount=0.5)
    return part


# --------------------------------------------------------------------------
# column_screw
# --------------------------------------------------------------------------
def build_column_screw():
    collar = _cyl(COLLAR_D, COLLAR_H, COLLAR_Z0)
    # detent crown: symmetric V notches, flanks at 30 deg to the direction of travel
    tan_ramp = math.tan(math.radians(NOTCH_RAMP_DEG))
    r_apex = COLLAR_D / 2 - NOTCH_DEPTH
    r_out = COLLAR_D / 2 + 1.5
    half_w = (r_out - r_apex) / tan_ramp
    from build123d import Polygon

    notch = extrude(
        Plane.XY * Polygon((r_apex, 0), (r_out, half_w), (r_out, -half_w), align=None),
        amount=COLLAR_H + 2,
    )
    notch = Pos(0, 0, COLLAR_Z0 - 1) * notch
    for i in range(NOTCH_COUNT):
        collar = collar - Rot(0, 0, i * 360 / NOTCH_COUNT) * notch
    collar = collar - _end_chamfer(COLLAR_D, COLLAR_Z0, top=False, size=0.8)

    shank = _cyl(THREAD_MAJOR, THREAD_Z0 - COLLAR_Z1 + 0.1, COLLAR_Z1)
    thread, minor_d = threads.external_thread(
        THREAD_MAJOR, THREAD_PITCH, THREAD_LEN, THREAD_Z0
    )
    relief = _cyl(minor_d - 0.3, KNOB_UNDER_Z - THREAD_Z1 + 0.1, THREAD_Z1)
    knob = _cyl(KNOB_D, KNOB_H, KNOB_UNDER_Z)
    for i in range(12):
        a = math.radians(i * 30)
        knob = knob - _cyl(
            6.0, KNOB_H + 2, KNOB_UNDER_Z - 1,
            KNOB_D / 2 * math.cos(a), KNOB_D / 2 * math.sin(a),
        )
    part = collar + shank + thread + relief + knob
    part = part - _end_chamfer(KNOB_D, KNOB_TOP_Z, top=True, size=1.0)
    return Pos(SCREW_X, 0, 0) * part


# --------------------------------------------------------------------------
# detent_leaf
# --------------------------------------------------------------------------
def build_detent_leaf():
    """Local frame: x outward from the screw axis, y along the beam, z up."""
    root = Pos(LEAF_ROOT_T / 2, -(LEAF_L - LEAF_ROOT_L / 2), 0) * Box(
        LEAF_ROOT_T, LEAF_ROOT_L, LEAF_H, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    spring = Pos(LEAF_SPRING_T / 2, -LEAF_FREE_L / 2, 0) * Box(
        LEAF_SPRING_T, LEAF_FREE_L, LEAF_H, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    part = root + spring
    for cy in (-LEAF_L + 3.0, -LEAF_L + LEAF_ROOT_L - 3.0):
        rib = Pos(LEAF_ROOT_T / 2, cy, 0) * Box(
            LEAF_ROOT_T + 2 * LEAF_RIB, 1.2, LEAF_H,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        part = part + rib
    nub = Pos(0, -1.5, LEAF_H / 2) * Sphere(NUB_D / 2)
    part = part + nub
    return Pos(LEAF_X, 0, LEAF_BOT_Z) * part


# --------------------------------------------------------------------------
# post_guide
# --------------------------------------------------------------------------
def build_post_guide():
    part = _cyl(POST_D, POST_LEN, POST_BOTTOM_Z, POST_X)
    part = part - _end_chamfer(POST_D, POST_TOP_Z, POST_X, top=True, size=1.0)
    part = part - _end_chamfer(POST_D, POST_BOTTOM_Z, POST_X, top=False, size=1.0)
    return part


# --------------------------------------------------------------------------
# yoke
# --------------------------------------------------------------------------
def _yoke_end(sign: float):
    from build123d import Polygon

    x = sign * POST_X
    tower = _cyl(SKIRT_OD, TOWER_TOP_Z - SKIRT_RIM_Z, SKIRT_RIM_Z, x)
    flare = Pos(x, 0, SKIRT_RIM_Z) * Cone(
        SKIRT_OD / 2, TOWER_FLARE_D / 2, SADDLE_RIM_Z - SKIRT_RIM_Z,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    block = Pos(sign * (LANE_HALF + YOKE_HALF_L) / 2, 0, PEDESTAL_BOT_Z) * Box(
        YOKE_HALF_L - LANE_HALF, 2 * YOKE_HALF_D, BRIDGE_TOP_Z - PEDESTAL_BOT_Z,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    # 45 deg ramp under the saddle end so nothing overhangs in the print orientation
    ramp = extrude(
        Plane.XZ * Polygon(
            (sign * 68.0, PEDESTAL_BOT_Z + 0.5),
            (sign * 78.0, SKIRT_RIM_Z),
            (sign * 78.0, PEDESTAL_BOT_Z + 0.5),
            align=None,
        ),
        amount=YOKE_HALF_D,
        both=True,
    )
    return tower + flare + block + ramp


def build_yoke():
    from build123d import Polygon

    part = _yoke_end(1.0) + _yoke_end(-1.0)
    bridge = Pos(0, 0, BRIDGE_UNDER_Z) * Box(
        2 * LANE_HALF + 2, 2 * BRIDGE_HALF_D, BRIDGE_TOP_Z - BRIDGE_UNDER_Z,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    part = part + bridge

    # bar channel through both end blocks
    for sign in (1.0, -1.0):
        ch = Pos(sign * (LANE_HALF + 80.0) / 2, 0, SADDLE_RIM_Z) * Box(
            80.0 - LANE_HALF + 2, BAR_D + 3.0, BRIDGE_UNDER_Z - SADDLE_RIM_Z,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        part = part - ch

    # V saddles (90 deg included), apex relieved so print artifacts cannot set H_bar
    for sign in (1.0, -1.0):
        vee = Pos(sign * SADDLE_X, 0, 0) * extrude(
            Plane.YZ * Polygon(
                (0, SADDLE_APEX_Z),
                (SADDLE_DEPTH + 2, SADDLE_RIM_Z + 2),
                (-(SADDLE_DEPTH + 2), SADDLE_RIM_Z + 2),
                align=None,
            ),
            amount=8.0,
            both=True,
        )
        part = part - vee
        part = part - (
            Pos(sign * SADDLE_X, 0, SADDLE_APEX_Z) * Rot(0, 90, 0)
            * Cylinder(SADDLE_RELIEF_D / 2, 16.0)
        )

    # screw tower: cavity, 45 deg cone, nut thread, clearance bore
    part = part - _cyl(SKIRT_ID, CAVITY_TOP_Z - SKIRT_RIM_Z, SKIRT_RIM_Z, -POST_X)
    part = part - (
        Pos(-POST_X, 0, CAVITY_TOP_Z) * Cone(
            SKIRT_ID / 2, NUT_MAJOR / 2, (SKIRT_ID - NUT_MAJOR) / 2,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
    )
    cut, nut_minor = threads.nut_cut(
        THREAD_MAJOR, THREAD_PITCH, NUT_LEN, NUT_Z0, NUT_FLANK_CLEARANCE, NUT_MAJOR
    )
    part = part - Pos(-POST_X, 0, 0) * cut
    part = part - _cyl(THREAD_MAJOR + 1.4, TOWER_TOP_Z - NUT_Z1 + 1, NUT_Z1, -POST_X)

    # post tower: one blind bore, 54 deep
    part = part - _cyl(POST_BORE_D, POST_BORE_DEPTH, SKIRT_RIM_Z - 0.001, POST_X)

    # lead-in chamfers on both skirt rims (§6 step 4)
    part = part - _bore_lead_in(SKIRT_ID, SKIRT_RIM_Z, -POST_X, up=False)
    part = part - _bore_lead_in(POST_BORE_D, SKIRT_RIM_Z, POST_X, up=False)
    return part


# --------------------------------------------------------------------------
# stop_ring / knob_hood / rail / piece
# --------------------------------------------------------------------------
def build_stop_ring():
    part = _tube(RING_OD, RING_ID, RING_H, 0.0, SCREW_X)
    return chamfer(part.edges().group_by(Axis.Z)[-1], 0.4)


def build_knob_hood():
    shell = _tube(HOOD_OD, HOOD_OD - 2 * HOOD_WALL, HOOD_TOP_Z - HOOD_RIM_Z, HOOD_RIM_Z, SCREW_X)
    ceiling = _cyl(HOOD_OD, HOOD_WALL, HOOD_CEIL_Z, SCREW_X)
    ledge = _tube(
        HOOD_LEDGE_D + 2 * 2.0, HOOD_LEDGE_D, HOOD_LEDGE_DEPTH,
        HOOD_CEIL_Z - HOOD_LEDGE_DEPTH, SCREW_X,
    )
    part = shell + ceiling + ledge
    tab = Pos(SCREW_X, HOOD_OD / 2 - 1, HOOD_TOP_Z - 14.0) * Box(
        HOOD_TAB_W, 10.0, 12.0, align=(Align.CENTER, Align.MIN, Align.MIN)
    )
    part = part + fillet(tab.edges().filter_by(Axis.Z), 3.0)
    part = fillet(part.edges().group_by(Axis.Z)[-1], 1.2)
    return part


def build_rail():
    part = Box(RAIL_L, RAIL_D, RAIL_T, align=(Align.CENTER, Align.CENTER, Align.MIN))
    for i in range(POCKET_N):
        cx = (i - (POCKET_N - 1) / 2) * POCKET_PITCH
        part = part - Pos(cx, 0, RAIL_T - POCKET_DEPTH) * Box(
            POCKET, POCKET, POCKET_DEPTH + 1, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
    part = chamfer(part.edges().filter_by(Axis.Z), 1.0)
    return part


_PIPS = {
    1: ((0, 0),),
    2: ((-1, -1), (1, 1)),
    3: ((-1, -1), (0, 0), (1, 1)),
    4: ((-1, -1), (-1, 1), (1, -1), (1, 1)),
    5: ((-1, -1), (-1, 1), (0, 0), (1, -1), (1, 1)),
}


def build_piece(height: float, set_index: int):
    part = Box(PIECE, PIECE, height, align=(Align.CENTER, Align.CENTER, Align.MIN))
    part = chamfer(part.edges().filter_by(Axis.Z), PIECE_CHAMFER)
    for px, pz in _PIPS[set_index + 1]:
        part = part - (
            Pos(px * PIP_PITCH, -PIECE / 2, height / 2 + pz * PIP_PITCH)
            * Rot(90, 0, 0)
            * Cylinder(PIP_D / 2, 2 * PIP_DEPTH)
        )
    return part


# --------------------------------------------------------------------------
# golden test article (brief "physics question to prove first")
# --------------------------------------------------------------------------
def build_golden_stub():
    plate = Pos(SCREW_X, 0, -BASE_T) * Box(
        60, 60, BASE_T, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    part = plate + _tube(SHROUD_OD, JOURNAL_D, SHROUD_TOP_Z, 0.0, SCREW_X)
    pad = Pos(LEAF_X + 0.5, -17.0, LEAF_BOT_Z - 0.5) * Box(
        LEAF_SOCKET_T + 6, LEAF_L + 4, (-BASE_T) - (LEAF_BOT_Z - 0.5),
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    part = part + pad
    # dial-indicator post: D12 x 90, clamped by nothing, 20 mm off the screw axis
    post = _cyl(12.0, 90.0, -BASE_T, SCREW_X + 24.0, 22.0)
    part = part + post
    part = part - screw_bore_cut(SHROUD_TOP_Z)
    part = part - leaf_pocket_cut()
    return part


# --------------------------------------------------------------------------
# the block ladder (§5.2) — regenerated per copy from the MEASURED H_top
# --------------------------------------------------------------------------
def piece_ladder(h_top: float = H_TOP_NOM, seed: int = 30003):
    """5 sets x 6 blocks drawn from the 42-rung ladder H = h_top - 0.25 - 0.5m."""
    import random

    rungs = [round(h_top - 0.25 - 0.5 * m, 3) for m in range(42)]
    rng = random.Random(seed)
    out: dict[str, float] = {}
    for si, key in enumerate(SET_KEYS):
        while True:
            pick = sorted(rng.sample(rungs, 6), reverse=True)
            if pick[0] <= h_top - 5.0:
                continue
            if pick[-1] >= h_top - 16.0:
                continue
            if any(abs(a - b) < 1.0 for a, b in zip(pick, pick[1:])):
                continue
            break
        for i, h in enumerate(pick):
            out[f"piece_{key}{i + 1}"] = h
    return out


PART_IDS = (
    ["gantry_base", "column_screw", "detent_leaf", "post_guide", "yoke", "stop_ring",
     "knob_hood"]
    + [f"rail_{i:02d}" for i in range(1, 5)]
    + list(piece_ladder().keys())
)

COLORS = {
    "gantry_base": "#b9bcc0",
    "column_screw": "#3f4550",
    "detent_leaf": "#e0533d",
    "post_guide": "#3f4550",
    "yoke": "#eceff2",
    "stop_ring": "#e0533d",
    "knob_hood": "#2b3038",
    "rail": "#8f949b",
    "piece": "#d8b26a",
    "bar": "#15181c",
}


def part_colors() -> dict[str, str]:
    out = {}
    for pid in PART_IDS:
        if pid.startswith("rail"):
            out[pid] = COLORS["rail"]
        elif pid.startswith("piece"):
            out[pid] = COLORS["piece"]
        else:
            out[pid] = COLORS[pid]
    return out


# --------------------------------------------------------------------------
# assembly placement
# --------------------------------------------------------------------------
# Mid-travel render pose. H_bar is chosen so the nut's helix phase matches the
# screw's exactly (the offset is a whole number of pitches) and a detent notch
# is seated: 25.35 = 9.35 + 8 x 2.00.
H_BAR_RENDER = 25.35


def build_bar():
    """buy_not_print: carbon-fibre tube D8 x D6 x 158, shown for context."""
    part = Rot(0, 90, 0) * _cyl(BAR_D, BAR_LEN, -BAR_LEN / 2)
    part = part - (Rot(0, 90, 0) * _cyl(6.0, BAR_LEN + 2, -BAR_LEN / 2 - 1))
    return Pos(0, 0, H_BAR_RENDER + BAR_AXIS_Z) * part
