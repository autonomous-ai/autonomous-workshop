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
THREAD_MINOR_D = THREAD_MAJOR - 5 * (THREAD_PITCH * math.sqrt(3) / 2) / 4   # 13.835
RELIEF_D = THREAD_MINOR_D - 0.3                                             # 13.535

# --------------------------------------------------------------------------
# 3. Gantry base
# --------------------------------------------------------------------------
BASE_L = 220.0
BASE_D = 78.0
BASE_T = 10.0
BASE_SKIN = 3.0                # runway skin over the ribbed underside
FOOT_D = 16.0
FOOT_H = 3.5
FEET = ((-100.0, -30.0), (100.0, -30.0), (0.0, 30.0))   # two front corners, one rear centre
LANE_HALF = 65.1               # lane clear half-width; 130.2 = 130.0 +0.5/-0.0

COLLAR_D = 24.0                # [DEV] detent crown and journal collar are ONE collar
COLLAR_H = 8.0
COLLAR_Z0 = -9.0               # collar bottom rests on the journal floor
COLLAR_Z1 = COLLAR_Z0 + COLLAR_H
JOURNAL_D = COLLAR_D + 0.40    # running clearance 0.40 diametral (brief fit class)
JOURNAL_DEPTH = 9.0            # below the runway
SHROUD_OD = 28.0               # [DEV] 24.0 -> 28.0; the D24 collar must pass the bore
# [DEV] the shroud is its own printed part. The runway has to be the bed face
# (brief §4 "matte light-grey runway with bed texture", §9.1 flatness datum), so
# the base prints runway-down — and a 24 mm tower cannot point at the bed. The
# shroud carries the journal bore, so journal/shroud coaxiality is now one part's
# problem instead of an assembly stack.
SHROUD_Z0 = -JOURNAL_DEPTH      # the shroud reaches down to the journal floor
SHROUD_SOCKET_D = SHROUD_OD - 0.10     # 0.10 interference -> light press
NOTCH_COUNT = 4
NOTCH_DEPTH = 0.80
NOTCH_RAMP_DEG = 30.0          # flank angle to the direction of travel (§3.5)

POST_D = 12.00
# [DEV] 82 -> 71. The brief sized the post against the TOP stop only. The yoke's
# post bore is blind at the top and travels DOWN with the yoke, so the binding
# case is the BOTTOM stop: bore ceiling = skirt rim + depth = 2.5 + 54 = 56.5,
# against a post top at 70. The brief's post is 13.5 mm too long. Fixed by
# deepening the bore to 60 (yoke height 62, exactly the brief's envelope) and
# shortening the post so its top sits 1.5 mm under the ceiling at the bottom stop.
POST_LEN = 71.0
POST_SOCKET_D = 11.90          # 0.10 interference -> transition/light press
POST_SOCKET_DEPTH = 10.0
POST_BOTTOM_Z = -BASE_T
POST_TOP_Z = POST_BOTTOM_Z + POST_LEN      # +61.0

LEAF_L = 34.0
LEAF_H = 12.0                  # the spring's width b; vertical when installed
LEAF_ROOT_T = 4.0
LEAF_SPRING_T = 1.60           # the tuning dimension (§3.5)
LEAF_FREE_L = 24.0
LEAF_ROOT_L = LEAF_L - LEAF_FREE_L
LEAF_SOCKET_T = 4.30
LEAF_RIB = 0.20                # per side: ribbed root 4.40 in a 4.30 socket = 0.10 interference
NUB_D = 3.0
LEAF_TOP_Z = -0.30             # just under the runway, so the stop ring never touches it
LEAF_BOT_Z = LEAF_TOP_Z - LEAF_H
# Where a D3.0 ball actually seats in the V. The notch flanks stand 60 deg off
# radial, so a ball of radius 1.5 touches both flanks with its CENTRE
# 1.5/sin(60) = 1.732 above the apex, not 1.5 — it never reaches the apex.
NOTCH_APEX_R = COLLAR_D / 2 - NOTCH_DEPTH                          # 11.2
NUB_SEAT_R = NOTCH_APEX_R + (NUB_D / 2) / math.sin(math.radians(60.0))   # 12.932
NUB_CREST_R = COLLAR_D / 2 + NUB_D / 2                             # 13.5, riding the crest
LEAF_PRELOAD = 0.40            # radial squeeze still left when the ball is seated
LEAF_FACE_R = NUB_SEAT_R - LEAF_PRELOAD                            # 12.532, FREE state
LEAF_X = SCREW_X + LEAF_FACE_R
LEAF_Y = 1.5                   # puts the nub on the screw's y = 0 plane, not 1.5 off it
NUB_Z = LEAF_TOP_Z - LEAF_H / 2                        # -6.3, mid-collar
# click amplitude the leaf actually sees, seated -> crest
LEAF_STROKE = NUB_CREST_R - NUB_SEAT_R                             # 0.568

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
NUT_LEAD_IN = 2.00             # thread cut runs this far below NUT_Z0, into the cone's void
POST_BORE_D = 12.40           # running clearance 0.40 diametral
POST_BORE_DEPTH = 60.0         # [DEV] 54 -> 60, see POST_LEN
POST_BORE_TOP_Z = SKIRT_RIM_Z + POST_BORE_DEPTH   # +45
POST_TOWER_TOP_Z = POST_BORE_TOP_Z + 2.0          # +47 -> yoke is 62 tall, per brief
SCREW_TOWER_TOP_Z = NUT_Z1 + 2.0                  # +36.65; above this is the top stop
TOP_STOP_BORE_D = THREAD_MAJOR + 1.4              # 17.4 clearance bore over the nut
PEDESTAL_BOT_Z = -5.0

# THE HARD TOP STOP. The brief names one ("H_top = bar height at the hard top
# stop") but never says which feature makes it, and the post cannot: a blind bore
# that travels down with the yoke can only ever be a BOTTOM stop. So the stop is
# the yoke's screw-tower rim seating on a 45 deg cone under the knob — line
# contact on a cone, self-centring, and it lands where the cone reaches the
# tower's D17.4 bore. Solve that for H_top = 33.000 and the cone starts here:
FLARE_Z0 = H_TOP_NOM + SCREW_TOWER_TOP_Z - (TOP_STOP_BORE_D - RELIEF_D) / 2
FLARE_D1 = RELIEF_D + 2 * (KNOB_UNDER_Z - FLARE_Z0)     # 30.10 where it meets the knob

# --------------------------------------------------------------------------
# 5. Stop ring, hood, rails, blocks
# --------------------------------------------------------------------------
RING_OD = 36.0
RING_ID = SHROUD_OD + 0.6
RING_H = 2.35                  # per copy (§5.3): skirt-rim Z at top stop - 15.50 - 0.15

HOOD_OD = 82.0
HOOD_WALL = 1.6
HOOD_TOP_Z = 92.4
HOOD_RIM_Z = HOOD_TOP_Z - 84.0                    # 8.4 -> the brief's 84 mm shell
HOOD_SEAT_Z = KNOB_TOP_Z                          # rests on the knob top face, Z = 90
HOOD_LEDGE_D = 44.40                              # +0.20/-0.00 over the D44 knob
# [DEV] a 45 deg conical roof replaces the 10 mm downward-hanging ledge ring:
# a ring hanging in mid-air needs support inside the very cavity that must stay
# clean. The cone's inner surface passes D44.40 exactly at Z = 90, so the hood
# self-centres on the knob's top edge and hangs from the KNOB (§4.2).
# The roof is CLOSED — see HOOD_CAP_T. The hood therefore prints ROOF-DOWN, not
# rim-down: the D47.6 cap is the first layer, the cone is a 45 deg expanding
# overhang above it, and the port/relief/rim are all open at the top of the
# print, so nothing bridges anywhere.
HOOD_CONE_BOT_Z = 75.2
HOOD_APEX_OD = HOOD_LEDGE_D + 2 * HOOD_WALL       # 47.6
HOOD_CAP_T = HOOD_TOP_Z - HOOD_SEAT_Z             # 2.4 of solid roof over the knob
HOOD_PORT_W = 66.0                                # brief §2 hand port width
HOOD_PORT_LIP_Z = 58.0                            # brief §4.1 port top lip
HOOD_TAB_W = 26.0
HOOD_TAB_BOT_Z = HOOD_TOP_Z - 30.0                # 62.4
HOOD_TAB_TOP_Z = HOOD_TAB_BOT_Z + 12.0            # 74.4
HOOD_TAB_OUT = 10.0                               # radial protrusion past D80
HOOD_RELIEF_HALF_D = 13.0                         # lane-side slot for the yoke bridge
HOOD_RELIEF_TOP_Z = 51.0                          # bridge top at H_top (33.0 + 17.0) + 1

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
    assert abs(JOURNAL_D - COLLAR_D - 0.40) < 1e-9, "collar/journal running fit"
    assert abs(POST_D - POST_SOCKET_D - 0.10) < 1e-9, "post press fit into the base"
    assert abs(POST_BORE_D - POST_D - 0.40) < 1e-9, "post/yoke running fit"
    assert SHROUD_OD + 1.0 <= SKIRT_ID, "shroud must telescope inside the yoke skirt"
    assert JOURNAL_D + 0.2 <= SHROUD_OD - 2 * 1.6, "the collar must pass the shroud bore"
    assert RING_OD > SKIRT_OD, "the skirt rim has to land on the ring"
    assert RING_ID > SHROUD_OD, "the ring drops over the shroud"
    # brief §1 datum stack: skirt rim sits at Z = 18.0 at H_top, 2.5 at H_bottom
    assert abs((H_TOP_NOM + SKIRT_RIM_Z) - 18.0) < 1e-9, "skirt rim Z at the top stop"
    assert abs((H_BOTTOM_NOM + SKIRT_RIM_Z) - 2.5) < 1e-9, "skirt rim Z at the bottom stop"
    # Exactly TWO stops, one at each end, and neither may be reached early.
    # TOP: the yoke's screw-tower rim seats on the knob cone.
    assert abs(
        (H_TOP_NOM + SCREW_TOWER_TOP_Z) - (FLARE_Z0 + (TOP_STOP_BORE_D - RELIEF_D) / 2)
    ) < 1e-9, "the top stop does not land on H_TOP_NOM"
    assert FLARE_Z0 > THREAD_Z1, "the top-stop cone would eat the thread"
    # BOTTOM: the yoke's skirt rim lands on the stop ring, between 15.50 and
    # 15.75 mm of travel, so click 31 seats and click 32 refuses (§5.3).
    _ring_stop_travel = (H_TOP_NOM + SKIRT_RIM_Z) - RING_H
    assert TRAVEL <= _ring_stop_travel < TRAVEL + 0.25, (
        f"stop ring lands at {_ring_stop_travel:.2f} mm of travel, not 15.50-15.75"
    )
    # the blind post bore must NOT bottom out anywhere in the travel — the case
    # the brief missed is the BOTTOM stop, where the bore ceiling is lowest
    assert POST_TOP_Z + 1.0 <= H_BOTTOM_NOM + POST_BORE_TOP_Z, (
        f"post top {POST_TOP_Z} fouls the bore ceiling "
        f"{H_BOTTOM_NOM + POST_BORE_TOP_Z} at the bottom stop"
    )
    assert POST_TOP_Z > H_TOP_NOM + SKIRT_RIM_Z + 30.0, "post engagement too short at the top"
    # ...and nothing else may touch first
    assert H_BOTTOM_NOM + CAVITY_TOP_Z > SHROUD_TOP_Z - 15.5, "skirt cavity fouls the shroud"
    assert H_TOP_NOM + NUT_Z1 <= THREAD_Z1 + 2.0, "nut hangs too far off the thread at the top"
    assert SADDLE_X + 8 < YOKE_HALF_L, "saddles sit inside the end blocks"
    assert BAR_LEN > 2 * SADDLE_X, "the bar spans both saddles"
    assert 2 * YOKE_HALF_L <= BED and BASE_L <= BED
    assert LANE_HALF * 2 >= 130.0 and LANE_HALF * 2 <= 130.5, "lane 130 +0.5/-0.0"
    assert abs(cadfits.slot_for(LEAF_ROOT_T + 2 * LEAF_RIB, -0.05) - LEAF_SOCKET_T) < 1e-9, (
        "leaf snap: ribbed root 4.40 in a 4.30 socket = 0.10 interference"
    )
    # the yoke nut has to stay on the thread over the whole travel
    assert H_BOTTOM_NOM + NUT_Z0 >= THREAD_Z0 - 0.01, "nut runs off the thread at the bottom"
    assert H_TOP_NOM + NUT_Z0 + 12 <= THREAD_Z1, "not enough engagement at the top"
    # the leaf is always squeezed: free radius < seated radius < crest radius
    assert LEAF_FACE_R < NUB_SEAT_R < NUB_CREST_R, "the detent ball must stay preloaded"
    assert LEAF_STROKE > 0.5, "click amplitude too small to be felt"
    # hood: 84 mm shell, 45 deg roof, and it must clear the yoke at the top stop
    assert abs((HOOD_TOP_Z - HOOD_RIM_Z) - 84.0) < 1e-9, "hood height 84 (brief §2)"
    assert abs((HOOD_TOP_Z - HOOD_CONE_BOT_Z) - (HOOD_OD - HOOD_APEX_OD) / 2) < 1e-9, (
        "hood roof must be 45 deg to print roof-down without support"
    )
    # §4.1/§4.2 hidden state: NOTHING may see the knob from above. The roof is a
    # closed cap at least one wall thick over the whole D44.40 seat circle, and
    # the seat plane is the knob's top face, so the sightline is solid PLA.
    assert HOOD_CAP_T >= HOOD_WALL, "the roof must close over the knob (§4.1)"
    assert HOOD_APEX_OD >= HOOD_LEDGE_D, "the cap must span the whole seat circle"
    # printed roof-down, the tab's upper face is an overhang unless it is tapered
    # at 45 deg back into the shell
    assert HOOD_TAB_TOP_Z - HOOD_TAB_BOT_Z > HOOD_TAB_OUT, "tab taper runs past the tab"
    assert HOOD_RIM_Z > RING_H, "the hood must hang clear of the stop ring"
    assert HOOD_RELIEF_TOP_Z > H_TOP_NOM + BRIDGE_TOP_Z, "bridge relief too short"
    assert HOOD_RELIEF_HALF_D > BRIDGE_HALF_D, "bridge relief too narrow"
    # nothing but the bridge may cross the hood wall: check the yoke's outermost
    # corner inside the hood against the hood bore radius
    _corner_r = math.hypot(YOKE_HALF_L - abs(SCREW_X), YOKE_HALF_D)
    assert max(_corner_r, math.hypot(LANE_HALF - abs(SCREW_X), YOKE_HALF_D)) < (
        HOOD_OD / 2 - HOOD_WALL - 2.0
    ), "the yoke end block fouls the hood shell"


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


def shroud_socket_cut():
    """Base-side pocket the screw shroud presses into (0.10 interference)."""
    return _cyl(SHROUD_SOCKET_D, -SHROUD_Z0 + 1.0, SHROUD_Z0, SCREW_X)


def leaf_pocket_cut():
    """Leaf socket, its nub window into the journal, and the flex clearance."""
    slot = Pos(
        LEAF_X + LEAF_ROOT_T / 2, LEAF_Y - (LEAF_L + 0.2) / 2 + 0.1, LEAF_BOT_Z
    ) * Box(
        LEAF_SOCKET_T, LEAF_L + 0.2, LEAF_H + 1, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    return slot + nub_window_cut()


def nub_window_cut():
    """Channel the leaf's beam and nub reach the collar through.

    It has to be cut from the SHROUD as well as the base: the shroud now owns
    the journal wall, and the beam sits at r 12.53-14.13, inside it.
    """
    return Pos(SCREW_X + 11.0, LEAF_Y - 5.0, COLLAR_Z0 - 0.2) * Box(
        14.0, 10.0, -COLLAR_Z0, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )


def leaf_pad(bottom_z: float):
    """Local boss that gives the 12 mm leaf socket a floor inside a 10 mm plate."""
    return Pos(LEAF_X + 0.5, LEAF_Y - 17.0, LEAF_BOT_Z - 0.5) * Box(
        LEAF_SOCKET_T + 6, LEAF_L + 4, (LEAF_BOT_Z - 0.5) * -1 + bottom_z,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )


# --------------------------------------------------------------------------
# gantry_base
# --------------------------------------------------------------------------
def build_gantry_base():
    plate = Pos(0, 0, -BASE_T) * Box(
        BASE_L, BASE_D, BASE_T, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    plate = chamfer(plate.edges().filter_by(Axis.Z), 2.0)

    part = plate

    # Ribbed underside: 7 mm deep pockets, 3 mm runway skin, 3 mm ribs. The base
    # prints runway-DOWN, so every one of these pockets is an upward-facing
    # recess — nothing here is bridged.
    pockets = None
    rib = 3.0
    cell = 24.0                # bridged ceiling span; kept under the 25 mm rule
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
            if abs(cx - LEAF_X) < 22 and LEAF_Y - 40 < cy < LEAF_Y + 6:
                continue
            # keep a solid pad under every foot; a foot over a pocket is a
            # boss standing on nothing once the part is flipped for printing
            if any(math.hypot(cx - fx, cy - fy) < 24 for fx, fy in FEET):
                continue
            p = Pos(cx, cy, -BASE_T) * Box(
                cell, cell, BASE_T - BASE_SKIN, align=(Align.CENTER, Align.CENTER, Align.MIN)
            )
            pockets = p if pockets is None else pockets + p
    part = part - pockets
    part = part + leaf_pad(-BASE_T)

    for fx, fy in FEET:
        foot = _cyl(FOOT_D, FOOT_H, -BASE_T - FOOT_H, fx, fy)
        # 1 mm taper on the free end: printed runway-down this is the LAST
        # feature laid, and a hard rim there is what scuffs a table
        foot = foot - _end_chamfer(FOOT_D, -BASE_T - FOOT_H, fx, top=False, size=1.0).moved(
            Location((0, fy, 0))
        )
        part = part + foot

    part = part - shroud_socket_cut()
    part = part - leaf_pocket_cut()
    part = part - _cyl(POST_SOCKET_D, POST_SOCKET_DEPTH + 1, -BASE_T - 0.5, POST_X)

    # lead-in chamfers (§6 step 4): two blind alignments have to be made at once
    part = part - _bore_lead_in(SHROUD_SOCKET_D, RUNWAY_Z, SCREW_X)
    part = part - _bore_lead_in(POST_SOCKET_D, RUNWAY_Z, POST_X)

    # the setter's ritual, embossed on the front skirt (§7.6)
    for k, line in enumerate(RITUAL_LINES):
        sk = Plane.XZ.offset(BASE_D / 2) * Pos(0, -3.0 - 2.8 * k) * Text(
            line, font_size=2.2, align=(Align.CENTER, Align.CENTER)
        )
        part = part + extrude(sk, amount=0.5)
    return part


# --------------------------------------------------------------------------
# screw_shroud  [DEV] — split out of gantry_base so the runway can be the bed face
# --------------------------------------------------------------------------
def build_screw_shroud(pressed: bool = False):
    """D28 tube, Z -9 .. +24. Its bore IS the journal, so coaxiality is internal.

    ``pressed=True`` returns the ASSEMBLED shape: the 0.10 mm interference band
    is already given up to the socket, which is what a press fit physically does
    once it is home. The printed part (``pressed=False``) keeps the interference.
    """
    part = _tube(SHROUD_OD, JOURNAL_D, SHROUD_TOP_Z - SHROUD_Z0, SHROUD_Z0, SCREW_X)
    # press-fit lead-in on the plug end, running lead-in on the screw's entry
    part = part - _end_chamfer(SHROUD_OD, SHROUD_Z0, SCREW_X, top=False, size=0.8)
    part = part - _end_chamfer(SHROUD_OD, SHROUD_TOP_Z, SCREW_X, top=True, size=0.8)
    part = part - _bore_lead_in(JOURNAL_D, SHROUD_TOP_Z, SCREW_X)
    part = part - nub_window_cut()
    if pressed:
        part = part - _press_band(SHROUD_OD, SHROUD_SOCKET_D, SHROUD_Z0, -SHROUD_Z0, SCREW_X)
    return part


def _press_band(od: float, socket_d: float, z0: float, h: float, x: float = 0.0):
    """The interference ring a press fit gives up on the way in."""
    return _cyl(od + 2, h, z0, x) - _cyl(socket_d - 0.02, h, z0, x)


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
    # Plane.XY * <sketch> faces -Z here, so extrude runs downward. Seat the wedge
    # off its own bounding box instead of assuming a direction — getting this
    # wrong puts the notches below the collar and the screw has no click at all.
    notch = Pos(0, 0, COLLAR_Z0 - 1 - notch.bounding_box().min.Z) * notch
    assert abs(notch.bounding_box().min.Z - (COLLAR_Z0 - 1)) < 1e-9
    for i in range(NOTCH_COUNT):
        collar = collar - Rot(0, 0, i * 360 / NOTCH_COUNT) * notch
    collar = collar - _end_chamfer(COLLAR_D, COLLAR_Z0, top=False, size=0.8)

    # Plain shank below the thread. Held 0.6 under the major so its OD is never
    # tangent to the thread crest — a tangent fuse leaves OCC with two solids.
    # It runs 2 mm INTO the thread so the first turn starts from full material.
    shank = _cyl(THREAD_MAJOR - 0.6, THREAD_Z0 + 2.0 - COLLAR_Z1, COLLAR_Z1)
    thread, minor_d = threads.external_thread(
        THREAD_MAJOR, THREAD_PITCH, THREAD_LEN, THREAD_Z0
    )
    assert abs(minor_d - THREAD_MINOR_D) < 1e-6, "thread minor diameter drifted"
    relief = _cyl(RELIEF_D, FLARE_Z0 - THREAD_Z1 + 0.1, THREAD_Z1)
    # the top-stop cone; also carries the knob's underside so it is a 7 mm ring
    # rather than a 15 mm unsupported shelf (the screw prints knob-up)
    relief = relief + Pos(0, 0, FLARE_Z0) * Cone(
        RELIEF_D / 2, FLARE_D1 / 2, KNOB_UNDER_Z - FLARE_Z0,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
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
def build_detent_leaf(seated: bool = False):
    """Local frame: x outward from the screw axis, y along the beam, z up.

    ``seated=True`` is the ASSEMBLED shape: snap ribs given up to the socket and
    the beam sprung out by ``LEAF_PRELOAD`` so the ball rides in a notch.
    """
    root = Pos(LEAF_ROOT_T / 2, -(LEAF_L - LEAF_ROOT_L / 2), 0) * Box(
        LEAF_ROOT_T, LEAF_ROOT_L, LEAF_H, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    # only the cantilever moves when the ball is seated; the root stays in its socket
    dx = LEAF_PRELOAD if seated else 0.0
    spring = Pos(LEAF_SPRING_T / 2 + dx, -LEAF_FREE_L / 2, 0) * Box(
        LEAF_SPRING_T, LEAF_FREE_L, LEAF_H, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    part = root + spring
    rib_t = LEAF_SOCKET_T - 0.02 if seated else LEAF_ROOT_T + 2 * LEAF_RIB
    for cy in (-LEAF_L + 3.0, -LEAF_L + LEAF_ROOT_L - 3.0):
        rib = Pos(LEAF_ROOT_T / 2, cy, 0) * Box(
            rib_t, 1.2, LEAF_H, align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        part = part + rib
    nub = Pos(dx, -NUB_D / 2, LEAF_H / 2) * Sphere(NUB_D / 2)
    part = part + nub
    # LEAF_Y lands the nub on the screw's y = 0 plane, so both flanks of the V
    # see the same ball — an off-centre nub is an asymmetric click (§4.3)
    return Pos(LEAF_X, LEAF_Y, LEAF_BOT_Z) * part


# --------------------------------------------------------------------------
# post_guide
# --------------------------------------------------------------------------
def build_post_guide(pressed: bool = False):
    part = _cyl(POST_D, POST_LEN, POST_BOTTOM_Z, POST_X)
    part = part - _end_chamfer(POST_D, POST_TOP_Z, POST_X, top=True, size=1.0)
    part = part - _end_chamfer(POST_D, POST_BOTTOM_Z, POST_X, top=False, size=1.0)
    if pressed:
        part = part - _press_band(POST_D, POST_SOCKET_D, POST_BOTTOM_Z, -POST_BOTTOM_Z, POST_X)
    return part


# --------------------------------------------------------------------------
# yoke
# --------------------------------------------------------------------------
def _yoke_end(sign: float, top_z: float):
    from build123d import Polygon

    x = sign * POST_X
    tower = _cyl(SKIRT_OD, top_z - SKIRT_RIM_Z, SKIRT_RIM_Z, x)
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
    return tower + block + ramp


def build_yoke():
    from build123d import Polygon

    part = _yoke_end(1.0, POST_TOWER_TOP_Z) + _yoke_end(-1.0, SCREW_TOWER_TOP_Z)
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
    # The 45 deg cone lands on D16.70 at exactly NUT_Z0, and the thread cut's own
    # bottom trim plane is that same circle at that same Z — two cut solids
    # tangent along one shared edge, which the tessellator turned into a 17-edge
    # crack (check_mesh: "FAIL watertight, 17 boundary edges"). Start the cut
    # NUT_LEAD_IN lower instead: at NUT_Z0 - 2.0 the cone has already opened to
    # R10.35, so the cut's bottom cap lands entirely in void and puts no face on
    # the part at all. The nut's threaded span (NUT_Z0..NUT_Z1) is unchanged.
    cut, nut_minor = threads.nut_cut(
        THREAD_MAJOR, THREAD_PITCH, NUT_LEN + NUT_LEAD_IN, NUT_Z0 - NUT_LEAD_IN,
        NUT_FLANK_CLEARANCE, NUT_MAJOR,
    )
    part = part - Pos(-POST_X, 0, 0) * cut
    part = part - _cyl(TOP_STOP_BORE_D, SCREW_TOWER_TOP_Z - NUT_Z1 + 1, NUT_Z1, -POST_X)

    # post tower: one blind bore, 54 deep
    part = part - _cyl(POST_BORE_D, POST_BORE_DEPTH, SKIRT_RIM_Z - 0.001, POST_X)

    # lead-in chamfers on both skirt rims (§6 step 4)
    part = part - _bore_lead_in(SKIRT_ID, SKIRT_RIM_Z, -POST_X, up=False)
    part = part - _bore_lead_in(POST_BORE_D, SKIRT_RIM_Z, POST_X, up=False)
    # §4.5: the yoke's lower edge nearest the post must not be a crisp pointer
    # against the post's layer lines. [DEV] 1.0 chamfer instead of R1.0 fillet —
    # same job, and it survives a boolean chain that a fillet selector does not.
    part = part - _end_chamfer(SKIRT_OD, SKIRT_RIM_Z, POST_X, top=False, size=1.0)
    return part


# --------------------------------------------------------------------------
# stop_ring / knob_hood / rail / piece
# --------------------------------------------------------------------------
def build_stop_ring():
    part = _tube(RING_OD, RING_ID, RING_H, 0.0, SCREW_X)
    return chamfer(part.edges().group_by(Axis.Z)[-1], 0.4)


def _hood_profile(od: float, rim_z: float, cone_bot_z: float, apex_od: float, top_z: float):
    """Cylinder + 45 deg cone, as one revolved-looking solid."""
    body = _cyl(od, cone_bot_z - rim_z, rim_z, SCREW_X)
    roof = Pos(SCREW_X, 0, cone_bot_z) * Cone(
        od / 2, apex_od / 2, top_z - cone_bot_z,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    return body + roof


def build_knob_hood():
    from build123d import Polygon

    outer = _hood_profile(
        HOOD_OD, HOOD_RIM_Z, HOOD_CONE_BOT_Z, HOOD_APEX_OD, HOOD_TOP_Z
    )
    # Inner surface offset down the 45 deg slope by one wall thickness. Dropping
    # it 2*WALL in Z gives WALL*sqrt(2)/2*2 = 1.6 mm measured normal to the cone.
    inner = _hood_profile(
        HOOD_OD - 2 * HOOD_WALL,
        HOOD_RIM_Z - 2.0,
        HOOD_CONE_BOT_Z - 2 * HOOD_WALL,
        HOOD_LEDGE_D,
        HOOD_SEAT_Z,
    )
    # The apex is NOT opened. `inner` stops at the D44.40 seat circle at Z = 90,
    # so everything above the knob's top face is solid: HOOD_CAP_T = 2.4 mm of
    # opaque PLA on the one sightline that would otherwise read the knob (§4.1).
    part = outer - inner

    # hand port: 66 wide, open to the bottom rim, ONE side, facing the setter (-Y).
    # [DEV] the top is a 45 deg gable peaking at the brief's Z = 58 lip instead of
    # a flat lintel — a 66 mm bridge printed rim-up would sag into the cavity.
    hw = HOOD_PORT_W / 2
    port = extrude(
        Plane.XZ * Polygon(
            (SCREW_X - hw, HOOD_RIM_Z - 2.0),
            (SCREW_X + hw, HOOD_RIM_Z - 2.0),
            (SCREW_X + hw, HOOD_PORT_LIP_Z - hw),
            (SCREW_X, HOOD_PORT_LIP_Z),
            (SCREW_X - hw, HOOD_PORT_LIP_Z - hw),
            align=None,
        ),
        amount=HOOD_OD,
        both=True,
    )
    setter_side = Pos(SCREW_X, -HOOD_OD / 2, 0) * Box(
        2 * HOOD_OD, HOOD_OD, 4 * HOOD_TOP_Z,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    part = part - (port & setter_side)

    # lane-side relief: the yoke bridge has to pass through the shell at every
    # click. Registered in DEVIATIONS.md — it exposes only the skirt/shroud, which
    # every seat can already see, never the knob (Z 76-90, far above this slot).
    part = part - Pos(SCREW_X + HOOD_OD / 2, 0, HOOD_RIM_Z - 2.0) * Box(
        HOOD_OD, 2 * HOOD_RELIEF_HALF_D, HOOD_RELIEF_TOP_Z - HOOD_RIM_Z + 2.0,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    tab = Pos(SCREW_X, HOOD_OD / 2 - 1, HOOD_TAB_BOT_Z) * Box(
        HOOD_TAB_W, HOOD_TAB_OUT, HOOD_TAB_TOP_Z - HOOD_TAB_BOT_Z,
        align=(Align.CENTER, Align.MIN, Align.MIN)
    )
    part = part + fillet(tab.edges().filter_by(Axis.Z), 3.0)
    # [DEV] printed roof-down, the tab's Z = 74.4 face points at the bed and a
    # flat 10 mm radial ledge there is an unsupported overhang. Taper it 45 deg:
    # the tab starts at the shell at 74.4 and reaches full protrusion by 64.4.
    # the cutter starts AT the OD, not at the tab's 1 mm root inset: one
    # millimetre further in it would notch a window through the 1.6 mm shell.
    y0 = HOOD_OD / 2
    taper = Pos(SCREW_X, 0, 0) * extrude(
        Plane.YZ * Polygon(
            (y0, HOOD_TAB_TOP_Z),
            (y0 + HOOD_TAB_OUT + 2, HOOD_TAB_TOP_Z - HOOD_TAB_OUT - 2),
            (y0 + HOOD_TAB_OUT + 2, HOOD_TOP_Z + 10),
            (y0, HOOD_TOP_Z + 10),
            align=None,
        ),
        amount=HOOD_OD,
        both=True,
    )
    part = part - taper
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
    """60 x 60 stub base + dial-indicator post. Print with column_screw,
    detent_leaf and screw_shroud and run brief tests 1-3 before the 34 h plate."""
    # 12.8 thick, not 10: the fixture prints runway-UP on a flat bottom, so the
    # leaf socket's floor is absorbed into the plate instead of hanging off it.
    stub_t = -(LEAF_BOT_Z - 0.5)
    part = Pos(SCREW_X, LEAF_Y, -stub_t) * Box(
        60, 60, stub_t, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    # dial-indicator post: D12 x 90, 24 mm off the screw axis, clear of the leaf
    part = part + _cyl(12.0, 90.0, -stub_t, SCREW_X + 24.0, 22.0)
    part = part - shroud_socket_cut()
    part = part - leaf_pocket_cut()
    part = part - _bore_lead_in(SHROUD_SOCKET_D, RUNWAY_Z, SCREW_X)
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


SETS = SET_KEYS
PIECE_LADDER = piece_ladder()


def _check_ladder(h_top: float = H_TOP_NOM) -> None:
    """§3.3: every block-vs-bar margin is >= 0.25 mm, and H_top cancels out."""
    bars = [h_top - 0.5 * k for k in range(32)]
    worst = min(abs(h - b) for h in PIECE_LADDER.values() for b in bars)
    assert worst >= 0.2499, f"margin guarantee broken: {worst:.4f} mm"
    for key in SET_KEYS:
        pick = [PIECE_LADDER[f"piece_{key}{i}"] for i in range(1, 7)]
        assert max(pick) > h_top - 5.0, f"set {key} has no high rung"
        assert min(pick) < h_top - 16.0, f"set {key} has no low rung"
        assert min(abs(a - b) for a in pick for b in pick if a != b) >= 1.0, (
            f"set {key} has two rungs within 1.0 mm"
        )


_check_ladder()


PART_IDS = (
    ["gantry_base", "screw_shroud", "column_screw", "detent_leaf", "post_guide",
     "yoke", "stop_ring", "knob_hood"]
    + [f"rail_{i:02d}" for i in range(1, 5)]
    + list(PIECE_LADDER.keys())
)

COLORS = {
    "gantry_base": "#b9bcc0",
    "screw_shroud": "#8f949b",
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
    return part


# --------------------------------------------------------------------------
# Assembly placement — every builder above is already in the ASSEMBLY frame
# except the yoke and the bar, which are built about H_bar.
# --------------------------------------------------------------------------
def asm_gantry_base():
    return build_gantry_base()


def asm_screw_shroud():
    return build_screw_shroud(pressed=True)


def asm_column_screw():
    return build_column_screw()


def asm_detent_leaf():
    """Shown SEATED, i.e. sprung out by LEAF_PRELOAD. The printed part is the
    free state (``build_detent_leaf``); the difference is the click force."""
    return build_detent_leaf(seated=True)


def asm_post_guide():
    return build_post_guide(pressed=True)


def asm_stop_ring():
    return build_stop_ring()


def asm_yoke(h_bar: float = H_BAR_RENDER):
    return Pos(0, 0, h_bar) * build_yoke()


def asm_bar(h_bar: float = H_BAR_RENDER):
    return Pos(0, 0, h_bar + BAR_AXIS_Z) * build_bar()


def asm_knob_hood():
    return build_knob_hood()


# --------------------------------------------------------------------------
# Print orientation — one part per file, bed datum at Z = 0, XY centred
# --------------------------------------------------------------------------
def _to_bed(shape):
    bb = shape.bounding_box()
    return Pos(-bb.center().X, -bb.center().Y, -bb.min.Z) * shape


def print_gantry_base():
    """Runway DOWN. The runway is the flatness datum (§9.1) and the brief asks
    for bed texture on it (§4); every socket then opens at the bed and every
    underside pocket faces up, so the part needs no support anywhere."""
    return _to_bed(Rot(180, 0, 0) * build_gantry_base())


def print_screw_shroud():
    return _to_bed(build_screw_shroud())


def print_column_screw():
    """Knob up, thread vertical, no supports on the thread (brief §2)."""
    return _to_bed(build_column_screw())


def print_detent_leaf():
    """Standing on its 34 x 4.4 edge: the beam bends in X, which is IN the layer
    plane. Laid on its side the click would load layer adhesion in tension."""
    return _to_bed(build_detent_leaf())


def print_post_guide():
    return _to_bed(build_post_guide())


def print_yoke():
    """Skirts down. Saddles, bar channel and both bores open upward or at the
    bed; the 130 mm bridge over the lane is the one supported feature."""
    return _to_bed(build_yoke())


def print_stop_ring():
    return _to_bed(build_stop_ring())


def print_knob_hood():
    """ROOF DOWN. The closed D47.6 cap is the first layer; the 45 deg cone above
    it is an expanding overhang; the hand port, the lane relief and the rim are
    all open at the TOP of the print, so nothing bridges. The tab's outer face is
    tapered 45 deg for the same reason (D4)."""
    return _to_bed(Rot(180, 0, 0) * build_knob_hood())


def print_rail():
    return _to_bed(build_rail())


def print_piece(part_id: str):
    """Standing, pips on one side face. Height comes from this copy's ladder."""
    return _to_bed(build_piece(PIECE_LADDER[part_id], SET_KEYS.index(part_id[-2])))


def print_golden_stub():
    return _to_bed(build_golden_stub())
