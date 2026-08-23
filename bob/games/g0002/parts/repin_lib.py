"""Re-Pin (g0002) — every dimension and every part builder.

All numbers come from games/g0002/parts_brief.md. Where a built value differs
from a brief value the reason is in ../cad/DEVIATIONS.md and it is marked [DEV]
here with the brief value in the comment.

Frames
------
ASSEMBLY frame: X = the plug axis, x = 0 at the plug's front face (the face the
key enters). Z = up. The chambers stand at 12 o'clock (+Z). The shell's foot
sits at Z = -34.0, so the plug axis is 34.0 above the base (brief §3).

Plug rotation is +theta about +X. A point at angle psi (measured from +Z toward
-Y) sits at (y, z) = (-r sin psi, r cos psi).

PART-LOCAL frames: the plug, the shell, the slug and the pins are all bodies of
revolution about the plug axis or about a chamber axis, so they are *built* with
the plug axis along +Z and the chamber direction along +Y, where profiles live
in XY and sweeps are about Z. ``TO_ASM`` maps that frame into the assembly
frame (z_local -> X, y_local -> Z, x_local -> Y). This is also the plug's print
orientation, which is why the plug is built there and printed there.
"""

from __future__ import annotations

import math

from build123d import (
    Align,
    Axis,
    Box,
    Cylinder,
    Location,
    Plane,
    Pos,
    Rot,
    Text,
    extrude,
    make_face,
    Polyline,
)

import cadfits

# ---------------------------------------------------------------------------
# 0. Frame transforms
# ---------------------------------------------------------------------------
# x_local -> Y, y_local -> Z, z_local -> X.  Rx(90) . Ry(90).
TO_ASM = Rot(90, 0, 0) * Rot(0, 90, 0)

# ---------------------------------------------------------------------------
# 1. The three radii that are the whole mechanism (brief §2)
# ---------------------------------------------------------------------------
R_PLUG = 22.0             # plug OD land
R_SHEAR = 22.4            # pin top / driver nose when a chamber is correct
R_BORE = 22.8             # shell bore
SHEAR_GAP = R_SHEAR - R_PLUG          # 0.40 below, C4
assert abs((R_BORE - R_SHEAR) - SHEAR_GAP) < 1e-6

# ---------------------------------------------------------------------------
# 2. The ladder (brief §4)
# ---------------------------------------------------------------------------
RUNGS = 8
LADDER_STEP = 1.2
PIN_H0 = 3.0
PIN_D = 6.20                          # -0.10/+0.00
PIN_HEIGHTS = tuple(round(PIN_H0 + LADDER_STEP * (r - 1), 3)
                    for r in range(1, RUNGS + 1))          # 3.0 .. 11.4

ROOF_R = 9.60                         # plug keyway roof / bore aperture plane
B_WORK = R_SHEAR - ROOF_R             # 12.80, C1
assert abs(B_WORK - 12.80) < 1e-6
assert abs(PIN_HEIGHTS[-1] + 1.4 - B_WORK) < 1e-6          # C2, with the brief's shortest lifter

# ---------------------------------------------------------------------------
# 3. Stop angles (brief §1) — the contract the mechanism has to hit
# ---------------------------------------------------------------------------
STOPS = (4.0, 20.0, 36.0, 52.0, 68.0)   # S0..S4: the stop for a wrong chamber 1..5
OPEN_ANGLE = 90.0
N_CHAMBERS = 5
CHAMBER_X = (24.0, 40.0, 56.0, 72.0, 88.0)   # from the plug's front face
CHAMBER_PITCH = 16.0
assert len(STOPS) == len(CHAMBER_X) == N_CHAMBERS
assert all(abs(b - a - CHAMBER_PITCH) < 1e-9 for a, b in zip(CHAMBER_X, CHAMBER_X[1:]))

# ---------------------------------------------------------------------------
# 4. Chamber feature sizes
# ---------------------------------------------------------------------------
BORE_D = 6.90                         # plug pin bore / shell guide bore / channel width
BORE_R = BORE_D / 2
PIN_CLEAR_RADIAL = (BORE_D - PIN_D) / 2                     # 0.35
APERTURE_D = 5.40                     # bore roof aperture
APERTURE_LEN = 0.80                   # [DEV] brief gives no length; 0.8 keeps the
                                      # shelf below the s=8 lifter top (see DEVIATIONS)
# [DEV] gate notch 3.40 -> 2.00 deep.  The notch floor is what caps how far a
# too-low driver falls, and that fall has to be small enough for the reset slide
# to lift it back inside one 16.0 chamber pitch (see LEVER_* and ../cad/
# DEVIATIONS.md "lever travel").  A 1-rung error still engages 1.20 - 0.40 =
# 0.80, which is the brief's own C5 number; deeper errors now cap at 2.00
# instead of 3.40, and every one of them still meets the end wall.
NOTCH_DEPTH = 2.00                    # gate notch, r 22.0 -> 20.0
NOTCH_FLOOR_R = R_PLUG - NOTCH_DEPTH                        # 18.60, C6
CHANNEL_OUTER_R = 32.20               # arc channel, r 22.8 -> 32.2
CHANNEL_DEPTH = CHANNEL_OUTER_R - R_BORE                    # 9.40, C7
SHOULDER_R = 34.60                    # the datum the driver flange rests on
DRIVER_BODY = SHOULDER_R - R_SHEAR                          # 12.20, C12
COUNTERBORE_D = 10.70
COUNTERBORE_TOP_R = 46.00
assert CHANNEL_DEPTH >= LADDER_STEP * (RUNGS - 1)           # C7: swallows 8.4
assert abs(SHOULDER_R - CHANNEL_OUTER_R - 2.40) < 1e-9      # C8

# The stop faces are tangent planes, not radial planes: a round nose/pin against
# a radial plane touches ~8 deg early and the stop angle then drifts with how far
# the part protrudes.  Offsetting the wall by the part's radius makes contact
# happen at exactly S for every rung.  [DEV] brief §2 says "radial end walls".
STOP_OFFSET = PIN_D / 2                                     # 3.10

# ---------------------------------------------------------------------------
# 5. Keyway and key (brief §3)
# ---------------------------------------------------------------------------
KEYWAY_W = 18.00
KEYWAY_H = 26.00
KEYWAY_ROOF_Y = ROOF_R                # +9.60
KEYWAY_FLOOR_Y = KEYWAY_ROOF_Y - KEYWAY_H                   # -16.40
KEYWAY_DEPTH = 98.0                   # blind; blade is 96 long (C11)

BLADE_W = 17.40                       # -0.10
BLADE_H = 25.40                       # -0.10
BLADE_LEN = 96.0
BLADE_ROOF_Y = KEYWAY_FLOOR_Y + BLADE_H                     # 9.00 - the blade rests
                                      # on the keyway floor, which is the hard datum
LIFTER_D = 4.80
# [DEV] brief lists lifter tops 1.4..9.8 above the blade roof, which assumes the
# blade roof sits at r = 9.60.  With the briefed 25.40 blade in the 26.00 keyway
# the blade seats on the keyway floor and its roof is at 9.00, so every lifter
# top moves up by 0.60.  Step, travel and B are unchanged.
LIFTER_TOP_Y = tuple(round(R_SHEAR - PIN_HEIGHTS[s - 1], 3)
                     for s in range(1, RUNGS + 1))          # 19.4 .. 11.0
LIFTER_H = tuple(round(t - BLADE_ROOF_Y, 3) for t in LIFTER_TOP_Y)   # 10.4 .. 2.0
LIFTER_TRAVEL = LIFTER_H[0] - LIFTER_H[-1]                  # 8.40, C3
assert abs(LIFTER_TRAVEL - LADDER_STEP * (RUNGS - 1)) < 1e-6
assert all(abs(LIFTER_TOP_Y[s - 1] + PIN_HEIGHTS[s - 1] - R_SHEAR) < 1e-6
           for s in range(1, RUNGS + 1))                    # s == r -> pin top on shear
SLIDER_PITCH = 4.00
SLIDER_TRAVEL = SLIDER_PITCH * (RUNGS - 1)                  # 28.0

# ---------------------------------------------------------------------------
# 6. Slug / driver (brief §3)
# ---------------------------------------------------------------------------
SLUG_NOSE_D = 6.20
SLUG_NOSE_L = DRIVER_BODY             # 12.20, nose face -> flange underside
SLUG_FLANGE_D = 10.00
SLUG_FLANGE_L = 6.00
SLUG_STEM_D = 7.00
SLUG_STEM_L = 10.00                   # [DEV] 12.0 -> 10.0; the top 2.0 becomes a head
SLUG_HEAD_D = 9.60                    # [DEV] new: the reset lever has to lift something
SLUG_HEAD_L = 2.00
SLUG_LEN = SLUG_NOSE_L + SLUG_FLANGE_L + SLUG_STEM_L + SLUG_HEAD_L
assert abs(SLUG_LEN - 30.20) < 1e-6   # envelope unchanged

# Every clearance below is derived, never typed twice (cadfits).
GUIDE_BORE_D = BORE_D                                        # 6.90 female
assert abs(cadfits.peg_for(GUIDE_BORE_D, PIN_CLEAR_RADIAL) - SLUG_NOSE_D) < 1e-9
COUNTERBORE_CLEAR = round((COUNTERBORE_D - SLUG_FLANGE_D) / 2, 3)     # 0.35
assert abs(cadfits.peg_for(COUNTERBORE_D, COUNTERBORE_CLEAR) - SLUG_FLANGE_D) < 1e-9

# ---------------------------------------------------------------------------
# 7. Plug body layout, along the local +Z (assembly +X), 0 at the front face
# ---------------------------------------------------------------------------
PLUG_LEN = 110.0
FLANGE_D = 70.0
FLANGE_L = 5.0
JOURNAL_D = 45.00
JOURNAL_R = JOURNAL_D / 2
JOURNAL_A = (7.0, 19.0)
JOURNAL_B = (101.0, 110.0)
CAM_Z = (94.0, 100.0)                  # latch cam lobe
CAM_R_MAX = 25.0
CAM_SPAN = (0.0, 22.0)                # plug-local phi; engaged over theta 68..90

CRADLE_D = 45.60                      # shell bore cradle
JOURNAL_CLEAR = round((CRADLE_D - JOURNAL_D) / 2, 3)                  # 0.30
assert abs(cadfits.peg_for(CRADLE_D, JOURNAL_CLEAR) - JOURNAL_D) < 1e-9
assert CRADLE_D / 2 == R_BORE

# ---------------------------------------------------------------------------
# 8. Shell layout (local frame: +Z = plug axis, +Y = chamber direction)
# ---------------------------------------------------------------------------
SHELL_Z0 = 5.5                        # front face, 0.5 clear of the pointer flange
SHELL_Z1 = 110.1                      # rear face.  110.1 - 110.0 (plug rear face)
                                      # + 0.40 cap spigot recess = 0.50 end float,
                                      # which is the brief's cap_01 number exactly.
SHELL_LEN = SHELL_Z1 - SHELL_Z0       # 105.0  (brief envelope 132 - fits)
SHELL_HALF_W = 39.0                   # 78 wide
BASE_Y = -34.0                        # foot underside; axis 34.0 above the base
FOOT_T = 4.0
BODY_OUTER_R = 35.20                  # >= 3.0 solid outside the 32.2 channels (§6)
assert BODY_OUTER_R - CHANNEL_OUTER_R >= 3.0

# Teardrop roof.  [DEV] brief asks for a 240-deg cradle + two 50-deg flanks; a
# 50-deg flank tangent to the clearance circle apexes at 35.8, above the 34.60
# shoulder datum, which destroys it.  Built: flanks tangent to r = 23.40 at
# +-45 deg (45 deg from vertical, self-supporting), apex 33.09, cradle 270 deg.
OGIVE_TANGENT_R = 23.40
OGIVE_TANGENT_PSI = 45.0
OGIVE_APEX_R = OGIVE_TANGENT_R / math.cos(math.radians(OGIVE_TANGENT_PSI))
assert OGIVE_TANGENT_R - R_PLUG >= 1.0                       # >= 1.0 clear of the plug
assert OGIVE_APEX_R < SHOULDER_R                             # roof stays under the datum

CHIMNEY_BAND = 10.0                   # local r=22.8 cylindrical bore at each chamber
DECK_HALF_W = 19.0
DECK_Y0 = 18.0
DECK_TOP_Y = COUNTERBORE_TOP_R        # 46.0
RAIL_H = 12.0
RAIL_W = 6.0
REBATE_Y = DECK_Y0                    # hood seats here
REBATE_DEPTH = 3.0

# ---------------------------------------------------------------------------
# 9. The rest of the bill
# ---------------------------------------------------------------------------
CAP_OD = 60.0
CAP_T = 8.0                           # plate 3.0 + tab 5.0 = the brief's 8.0
CAP_PLATE_T = 3.0
CAP_TAB_L = CAP_T - CAP_PLATE_T       # 5.0
CAP_BORE_D = 45.80                    # spigot recess over the plug's rear journal
CAP_SPIGOT_DEPTH = 0.40
CAP_SIGHT_D = 20.0
CAP_TAB = (12.0, 2.0)                 # tangential width, radial thickness
CAP_TAB_R = 30.0                      # pitch radius of the three tabs
CAP_ENGAGE = 1.20                     # nib height = snap engagement
CAP_TAB_FIT = 0.30                    # per side, tab in pocket
CAP_END_FLOAT = round(SHELL_Z1 - PLUG_LEN + CAP_SPIGOT_DEPTH, 3)
assert abs(CAP_END_FLOAT - 0.50) < 1e-9        # the brief's 0.5 axial end float
CAP_LEDGE_Z = SHELL_Z1 - 3.0          # the face the snap nib latches behind
CAP_NIB_Z = (3.0, 4.5)                # nib band, measured from the plate face
LEVER_DETENT_NIB_Z = 60.0             # shell z of the rail-groove detent nib

HOOD_SEAT = (66.4, 100.4)             # trench centreline rectangle on the shell
HOOD_L = HOOD_SEAT[1] + 2.5           # [DEV] 112 -> 102.9
HOOD_W = HOOD_SEAT[0] + 2.5           # [DEV] 72 -> 68.9
HOOD_SEAT_Y = 15.0                    # trench floor; skirt seats 3.0 into it
HOOD_WALL = 2.50
HOOD_CLEAR = 0.40
HOOD_HEADROOM = 30.0                  # brief: interior clear height above the
                                      # chimney tops (r = 46.0)
HOOD_CEIL_Y = DECK_TOP_Y + HOOD_HEADROOM                     # 76.0
HOOD_H = HOOD_CEIL_Y - HOOD_SEAT_Y + HOOD_WALL               # [DEV] 46 -> 63.5

# ---- lever_01, the reset slide -------------------------------------------
# The chimney pitch is 16.0, so the slide's travel and its ramp run both have to
# live inside 16.0 or a head ends up over its neighbour's loading hole.  That is
# the whole reason the brief's 0/20/40 detents and 1:4 ramp are not buildable
# here; see ../cad/DEVIATIONS.md "lever travel".
LEVER_L = 96.0
LEVER_W = 34.0
LEVER_Z0 = 4.0                        # front end at RUN (shell z); travel is +z
LEVER_SLOT_D = 7.60                   # stem slot, brief
LEVER_TUNNEL_W = 10.40                # head channel, 0.40 on the D9.60 head
LEVER_LEDGE_X = (LEVER_SLOT_D / 2, LEVER_TUNNEL_W / 2)       # 3.80 .. 5.20 ledge
LEVER_LOAD_D = 10.40                  # roof hole; the D10.00 slug flange passes
LEVER_Y0 = DECK_TOP_Y + 0.2           # 46.2 underside, 0.2 clear of the deck

# Head heights, all measured from the driver's nose (SLUG_* section 6):
SLUG_HEAD_BOT = SLUG_NOSE_L + SLUG_FLANGE_L + SLUG_STEM_L    # 28.20 above the nose
LEVER_TOP_Y = R_SHEAR + SLUG_HEAD_BOT                        # 50.60, a correct driver
LEVER_LOW_Y = LEVER_TOP_Y - NOTCH_DEPTH                      # 48.60, the lowest driver
LEVER_RAMP_Y0 = LEVER_LOW_Y - 0.2                            # 48.40 ramp mouth
LEVER_LIFT = round(LEVER_TOP_Y - LEVER_RAMP_Y0, 3)           # 2.20
# The driver rides up n x 1.2 when the stack is too tall, so the tunnel ceiling
# has to clear the tallest possible head, not the nominal one.
LEVER_RISE_MAX = LADDER_STEP * (RUNGS - 1)                   # 8.40
LEVER_ROOF_Y = LEVER_TOP_Y + SLUG_HEAD_L + LEVER_RISE_MAX + 0.4          # 61.40
LEVER_T = round(LEVER_ROOF_Y + 2.5 - LEVER_Y0, 3)            # [DEV] 9 -> 17.70
LEVER_Y1 = LEVER_Y0 + LEVER_T

# One 16.0 pitch holds: head clearance at RUN, the ramp, and a land.  Nothing
# else fits, which is why there are two detents and not the brief's three.
LEVER_RAMP = (5.3, 9.9)               # window start / ramp top, as -w from a chamber
LEVER_LAND = 1.0
LEVER_DETENTS = (0.0, LEVER_RAMP[1])  # RUN , LOAD/RESET   [DEV] 0/20/40
LEVER_RAMP_RUN = LEVER_RAMP[1] - LEVER_RAMP[0]               # 4.60
assert LEVER_RAMP[0] >= SLUG_HEAD_D / 2 + 0.3                # head clear at RUN
assert CHAMBER_PITCH - LEVER_RAMP[1] - LEVER_LAND >= SLUG_HEAD_D / 2 + 0.3
assert LEVER_TOP_Y - SLUG_HEAD_BOT >= R_SHEAR                # reset frees every nose
assert LEVER_ROOF_Y + 2.5 <= HOOD_CEIL_Y

LATCH_L = 80.0
LATCH_W = 14.0
LATCH_T = 9.0
LATCH_FLEX = (1.80, 24.0)
LATCH_NIB = (1.20, 0.80)
LATCH_CLEAR = 0.30                    # nose nib to plug land, sliding
LATCH_PRESS = 0.10                    # root interference in the seat, total
LATCH_RAMP_Y = 2.60                   # 1.5 x / 2.6 y = the brief's 30 deg face

PEG_D = 5.00
PEG_L = 14.0
SOCKET_D = 5.40                       # peg / socket: 0.20 per side, 0.40 diametral
assert abs(cadfits.slot_for(PEG_D, 0.20) - SOCKET_D) < 1e-9

TRAY_L, TRAY_W, TRAY_T = 120.0, 34.0, 10.0
BOARD_L, BOARD_W, BOARD_T = 150.0, 45.0, 6.0
CASE_L, CASE_W, CASE_T = 100.0, 66.0, 20.0
TUBE_D, TUBE_DEPTH = 7.40, 15.0

BED = 251.0


# ---------------------------------------------------------------------------
# 10. Geometry helpers — the angle convention, once
# ---------------------------------------------------------------------------
def _pt(r: float, phi_deg: float) -> tuple[float, float]:
    """Point at radius ``r``, angle ``phi`` measured from +Y toward -X."""
    a = math.radians(phi_deg)
    return (-r * math.sin(a), r * math.cos(a))


def _e_t(phi_deg: float) -> tuple[float, float]:
    """Unit tangent at ``phi`` — the direction the plug's surface travels."""
    a = math.radians(phi_deg)
    return (-math.cos(a), -math.sin(a))


def sector(r0: float, r1: float, phi0: float, phi1: float,
           z0: float, z1: float, steps: int = 48):
    """Annular sector solid about the local Z axis, phi0 -> phi1 (deg)."""
    outer = [_pt(r1, phi0 + (phi1 - phi0) * i / steps) for i in range(steps + 1)]
    inner = [_pt(r0, phi1 + (phi0 - phi1) * i / steps) for i in range(steps + 1)]
    face = make_face(Polyline(*[(p[0], p[1], 0.0) for p in outer + inner + [outer[0]]]))
    return Pos(0, 0, z0) * extrude(face, z1 - z0)


def stop_block(phi_stop: float, side: int, offset: float = STOP_OFFSET, big: float = 240.0):
    """Half-space that leaves a flat stop face tangent to a cylinder of radius
    ``offset`` whose axis is the ray at ``phi_stop``.

    ``side`` = +1 when the moving part approaches with increasing phi (the
    shell's arc channel), -1 when it approaches with decreasing phi (the plug's
    gate notch).  Contact then happens at exactly ``phi_stop`` for every radius,
    which a radial wall cannot do — see ../cad/DEVIATIONS.md "stop faces".
    """
    ang = phi_stop + 180.0 if side > 0 else phi_stop
    # local +X of the box maps to e_t(phi_stop) for side>0, to -e_t for side<0
    return (Rot(0, 0, ang) * Pos(offset + big / 2, 0, 0)
            * Box(big, 4 * big, 8 * big, align=Align.CENTER))


def engrave(txt: str, size: float, depth: float, plane, loc):
    """Sunk text on ``plane`` at ``loc`` (a Location applied after)."""
    face = plane * Text(txt, font_size=size, align=(Align.CENTER, Align.CENTER))
    return loc * extrude(face, -depth)


COLORS = {
    "plug_01": "#c9a227",
    "shell_01": "#8f949b",
    "cap_01": "#3f4550",
    "hood_01": "#2b3038",
    "latch_01": "#e0533d",
    "lever_01": "#e0533d",
    "slug_01": "#eceff2",
    "pin": "#d8b26a",
    "case_01": "#5b6169",
    "lid_01": "#5b6169",
    "key_01": "#b9bcc0",
    "tray_01": "#5b6169",
    "board_01": "#5b6169",
    "peg_01": "#e0533d",
    "gp1": "#7a8089",
}


def part_colors() -> dict[str, str]:
    out = {k: v for k, v in COLORS.items() if k.endswith("_01") or k == "gp1"}
    for r in range(1, RUNGS + 1):
        out[f"pin_r{r}"] = COLORS["pin"]
    return out


# ---------------------------------------------------------------------------
# 11. plug_01 — the part that turns the ladder into an angle
# ---------------------------------------------------------------------------
def _chamber_bore(zc: float):
    """Pin bore + roof aperture for one chamber, as a cutting solid."""
    neck = (Rot(-90, 0, 0) * Pos(0, 0, ROOF_R)
            * Cylinder(APERTURE_D / 2, APERTURE_LEN,
                       align=(Align.CENTER, Align.CENTER, Align.MIN)))
    bore = (Rot(-90, 0, 0) * Pos(0, 0, ROOF_R + APERTURE_LEN)
            * Cylinder(BORE_R, 40.0, align=(Align.CENTER, Align.CENTER, Align.MIN)))
    return Pos(0, 0, zc) * (neck + bore)


def _gate_notch(zc: float, stop_deg: float):
    """Gate notch for one chamber: a 6.90 x 3.40 circumferential slot whose far
    end is the tangent stop face at phi = -stop_deg."""
    phi_s = -stop_deg
    # The sector is a chorded polygon, so its outer edge must overshoot the D44
    # land or the cut leaves 0.0001 mm crescents of plug behind and the mesh is
    # not watertight.  Depth is set by the inner radius, which is exact.
    raw = sector(NOTCH_FLOOR_R, R_PLUG + 0.6, phi_s - 12.0, 7.0,
                 zc - BORE_R, zc + BORE_R)
    return raw - stop_block(phi_s, -1)


def _latch_cam():
    lo, hi = CAM_SPAN
    outer = []
    for i in range(25):
        phi = hi - (hi - lo) * i / 24
        r = R_PLUG + (CAM_R_MAX - R_PLUG) * (hi - phi) / (hi - lo)
        outer.append(_pt(r, phi))
    outer += [_pt(CAM_R_MAX, -6.0)]
    inner = [_pt(20.0, -6.0), _pt(20.0, hi)]
    pts = [(p[0], p[1], 0.0) for p in outer + inner + [outer[0]]]
    face = make_face(Polyline(*pts))
    cam = Pos(0, 0, CAM_Z[0]) * extrude(face, CAM_Z[1] - CAM_Z[0])
    # The click: at theta = 90 the latch nib (LATCH_NIB) is at plug-local phi = 0
    # and drops CAP-style into this groove.  Cut only outboard of the land, so the
    # plug's D44 surface is untouched.
    cam -= sector(CAM_DETENT[0], CAM_R_MAX + 1.0, -CAM_DETENT[1], CAM_DETENT[1],
                  CAM_Z[0] - 1.0, CAM_Z[1] + 1.0, steps=8)
    return cam


def build_plug():
    """plug_01 in the plug-local frame: +Z = axis, front face at z = 0,
    +Y = the chamber direction. This is also the print orientation."""
    p = Cylinder(FLANGE_D / 2, FLANGE_L, align=(Align.CENTER, Align.CENTER, Align.MIN))
    p += (Pos(0, 0, FLANGE_L)
          * Cylinder(R_PLUG, PLUG_LEN - FLANGE_L,
                     align=(Align.CENTER, Align.CENTER, Align.MIN)))
    for z0, z1 in (JOURNAL_A, JOURNAL_B):
        p += (Pos(0, 0, z0)
              * Cylinder(JOURNAL_R, z1 - z0, align=(Align.CENTER, Align.CENTER, Align.MIN)))
    p += _latch_cam()

    # pointer fin, riding over the shell's protractor plate
    POINTER_TIP = 38.5
    p += (Pos(0, (32.0 + POINTER_TIP) / 2, FLANGE_L / 2)
          * Box(4.0, POINTER_TIP - 32.0, FLANGE_L, align=Align.CENTER))

    # keyway: 18.00 W x 26.00 H, roof at r = 9.60, blind at 98
    p -= (Pos(0, (KEYWAY_ROOF_Y + KEYWAY_FLOOR_Y) / 2, KEYWAY_DEPTH / 2)
          * Box(KEYWAY_W, KEYWAY_H, KEYWAY_DEPTH, align=Align.CENTER))

    for zc, s in zip(CHAMBER_X, STOPS):
        p -= _chamber_bore(zc)
        p -= _gate_notch(zc, s)
    return p


def print_plug():
    return Pos(0, 0, 0) * build_plug()


def asm_plug(theta: float = 0.0):
    return TO_ASM * Rot(0, 0, theta) * build_plug()


# ---------------------------------------------------------------------------
# 12. shell_01 — the fixed half of the measurement
# ---------------------------------------------------------------------------
OGIVE_TANGENT_Y = OGIVE_TANGENT_R * math.cos(math.radians(OGIVE_TANGENT_PSI))
# The latch lies in a boss on the -X (Locksmith) flank, its 9.0 thickness radial
# and its 14.0 width vertical, so the flexure bends in the print plane.
LATCH_SEAT = dict(x0=-35.0, x1=-26.0, y0=-9.0, y1=5.0, z0=20.0, z1=SHELL_Z1 + 1)
LATCH_BOSS = dict(x0=-37.5, x1=-24.0, y0=-11.0, y1=7.0, z0=22.0, z1=106.0)
LATCH_WINDOW_Z = (86.0, 102.0)
LATCH_WINDOW_X = (-28.5, -19.0)
LATCH_NOSE_Z = (86.5, 100.0)                                 # inside the window
LATCH_FLEX_Z = (LATCH_NOSE_Z[0] - LATCH_FLEX[1], LATCH_NOSE_Z[0])   # 62.5 .. 86.5
LATCH_ROOT_Z = (20.0, LATCH_FLEX_Z[0])
LATCH_NOSE_X = -(R_PLUG + LATCH_CLEAR + LATCH_NIB[1])        # -23.10 nose face
LATCH_NIB_X = -(R_PLUG + LATCH_CLEAR)                        # -22.30 nib tip
assert CAM_R_MAX - (R_PLUG + LATCH_CLEAR) <= 3.0             # <= working deflection
CAM_DETENT = (24.20, 1.8)                                    # groove floor r, half-angle
DOVETAIL_MALE = ((13.0, 50.0), (17.0, 48.0), (17.0, 56.0), (13.0, 54.0))
DOVETAIL_FIT = 0.10                                          # transition, 0.20 total


def _prism_xy(pts, z0, z1):
    face = make_face(Polyline(*[(p[0], p[1], 0.0) for p in list(pts) + [pts[0]]]))
    return Pos(0, 0, z0) * extrude(face, z1 - z0)


def _teardrop_void():
    """Plug chamber: r = 22.8 cradle everywhere, plus a 45-deg self-supporting
    ogive roof between the chimney bands."""
    cradle = (Pos(0, 0, SHELL_Z0 - 1)
              * Cylinder(R_BORE, SHELL_LEN + 2, align=(Align.CENTER, Align.CENTER, Align.MIN)))
    apex = OGIVE_APEX_R
    wedge = _prism_xy([(-(apex - OGIVE_TANGENT_Y), OGIVE_TANGENT_Y),
                       (apex - OGIVE_TANGENT_Y, OGIVE_TANGENT_Y),
                       (0.0, apex)], SHELL_Z0 - 1, SHELL_Z1 + 1)
    for zc in CHAMBER_X:
        wedge -= Pos(0, 0, zc) * Box(200, 200, CHIMNEY_BAND, align=Align.CENTER)
    return cradle + wedge


def _chimney_cut(zc: float, stop_deg: float):
    guide = (Rot(-90, 0, 0) * Pos(0, 0, R_BORE)
             * Cylinder(GUIDE_BORE_D / 2, SHOULDER_R - R_BORE,
                        align=(Align.CENTER, Align.CENTER, Align.MIN)))
    cbore = (Rot(-90, 0, 0) * Pos(0, 0, SHOULDER_R)
             * Cylinder(COUNTERBORE_D / 2, COUNTERBORE_TOP_R - SHOULDER_R + 30.0,
                        align=(Align.CENTER, Align.CENTER, Align.MIN)))
    chan = sector(R_BORE - 0.6, CHANNEL_OUTER_R, -4.5, stop_deg + 12.0,
                  zc - BORE_R, zc + BORE_R) - stop_block(stop_deg, +1)
    return Pos(0, 0, zc) * (guide + cbore) + chan


def _protractor():
    cut = None
    for ang, label in zip(list(STOPS) + [OPEN_ANGLE], ["0", "1", "2", "3", "4", "OPEN"]):
        a = math.radians(ang)
        cx, cy = _pt(37.0, ang)
        tick = (Pos(cx, cy, SHELL_Z0 - 0.01) * Rot(0, 0, -ang)
                * Box(1.2, 3.0, 1.0, align=(Align.CENTER, Align.CENTER, Align.MIN)))
        tx, ty = _pt(41.5 if label == "OPEN" else 40.0, ang)
        txt = (Plane.XY.offset(SHELL_Z0 + 0.5) * Rot(0, 0, -ang)
               * Pos(tx, ty, 0)) * Text(label, font_size=3.6,
                                        align=(Align.CENTER, Align.CENTER))
        cut = tick if cut is None else cut + tick
    return cut


def build_shell():
    """shell_01 in the shell-local frame: +Z = plug axis, +Y = the chamber
    direction, z = 5.5 at the front face."""
    body = (Pos(0, 0, SHELL_Z0)
            * Cylinder(BODY_OUTER_R, SHELL_LEN, align=(Align.CENTER, Align.CENTER, Align.MIN)))
    for z0, z1 in ((SHELL_Z0, SHELL_Z0 + 4.0), (SHELL_Z1 - 4.0, SHELL_Z1)):
        body += (Pos(0, (BASE_Y + DECK_TOP_Y) / 2, (z0 + z1) / 2)
                 * Box(2 * SHELL_HALF_W, DECK_TOP_Y - BASE_Y, z1 - z0, align=Align.CENTER))
    body += (Pos(0, (DECK_Y0 + DECK_TOP_Y) / 2, (16.65 + 95.35) / 2)
             * Box(2 * DECK_HALF_W, DECK_TOP_Y - DECK_Y0, 95.35 - 16.65, align=Align.CENTER))
    body += (Pos(0, BASE_Y + FOOT_T / 2, (SHELL_Z0 + SHELL_Z1) / 2)
             * Box(2 * SHELL_HALF_W, FOOT_T, SHELL_LEN, align=Align.CENTER))
    for sx in (-1, 1):                                        # skirt webs, foot -> body
        body += (Pos(sx * 30.0, -19.0, (SHELL_Z0 + SHELL_Z1) / 2)
                 * Box(4.0, 30.0, SHELL_LEN, align=Align.CENTER))
    # hood seat flange + rails
    body += (Pos(0, HOOD_SEAT_Y + 1.5, (SHELL_Z0 + SHELL_Z1) / 2)
             * Box(2 * 36.0, 6.0, SHELL_LEN, align=Align.CENTER))
    for sx in (-1, 1):
        body += (Pos(sx * 16.0, DECK_TOP_Y + RAIL_H / 2, (16.65 + 95.35) / 2)
                 * Box(RAIL_W, RAIL_H, 95.35 - 16.65, align=Align.CENTER))
    b_ = LATCH_BOSS                                           # latch boss, -X flank
    body += (Pos((b_["x0"] + b_["x1"]) / 2, (b_["y0"] + b_["y1"]) / 2,
                 (b_["z0"] + b_["z1"]) / 2)
             * Box(b_["x1"] - b_["x0"], b_["y1"] - b_["y0"], b_["z1"] - b_["z0"],
                   align=Align.CENTER))

    # --- cuts ---
    body -= _teardrop_void()
    for zc, s in zip(CHAMBER_X, STOPS):
        body -= _chimney_cut(zc, s)
    # dovetail grooves in the rails (female = male + 0.10 per side)
    for sx in (-1, 1):
        pts = [(sx * (px + DOVETAIL_FIT * (1 if px > 14 else -1)),
                py + (DOVETAIL_FIT if py > 52 else -DOVETAIL_FIT))
               for px, py in DOVETAIL_MALE]
        body -= _prism_xy(pts, 10.0, 106.0)
    # hood trench: 3.0 wide, 3.0 deep, open on the -X (Locksmith) face
    hw, hl = HOOD_SEAT
    for box in (Box(HOOD_WALL + HOOD_CLEAR, 3.2, hl, align=Align.CENTER),):
        body -= Pos(hw / 2, HOOD_SEAT_Y + 1.6, (SHELL_Z0 + SHELL_Z1) / 2) * box
    for zc in (-hl / 2, hl / 2):
        body -= (Pos(0, HOOD_SEAT_Y + 1.6, (SHELL_Z0 + SHELL_Z1) / 2 + zc)
                 * Box(hw + 3.0, 3.2, HOOD_WALL + HOOD_CLEAR, align=Align.CENTER))
    # latch seat + follower window
    s_ = LATCH_SEAT
    body -= (Pos((s_["x0"] + s_["x1"]) / 2, (s_["y0"] + s_["y1"]) / 2,
                 (s_["z0"] + s_["z1"]) / 2)
             * Box(s_["x1"] - s_["x0"], s_["y1"] - s_["y0"], s_["z1"] - s_["z0"],
                   align=Align.CENTER))
    w_ = LATCH_WINDOW_X
    body -= (Pos((w_[0] + w_[1]) / 2, 0.0, sum(LATCH_WINDOW_Z) / 2)
             * Box(w_[1] - w_[0], 10.0, LATCH_WINDOW_Z[1] - LATCH_WINDOW_Z[0],
                   align=Align.CENTER))
    # cap snap-tab pockets in the rear face: 3 at 120 deg, each with an outward
    # ledge the cap's nib snaps behind (engagement CAP_ENGAGE).
    r_in = CAP_TAB_R - CAP_TAB[1] / 2 - CAP_TAB_FIT
    r_narrow = CAP_TAB_R + CAP_TAB[1] / 2 + CAP_TAB_FIT
    z_deep = SHELL_Z1 - (CAP_TAB_L + 0.4)
    for k in range(3):
        phi = 120.0 * k
        for r_out, z0, z1 in ((r_narrow, z_deep, SHELL_Z1 + 1.0),
                              (r_narrow + CAP_ENGAGE, z_deep, CAP_LEDGE_Z)):
            body -= (Rot(0, 0, phi)
                     * Pos(0, (r_in + r_out) / 2, (z0 + z1) / 2)
                     * Box(CAP_TAB[0] + 2 * CAP_TAB_FIT, r_out - r_in, z1 - z0,
                           align=Align.CENTER))
    # rail-groove detent nib: the lever's three notches click onto it
    for sx in (-1, 1):
        body += (Pos(sx * 14.6, 55.4, LEVER_DETENT_NIB_Z)
                 * Box(1.6, 0.6, 2.4, align=Align.CENTER))
    body -= _protractor()
    body -= (Pos(0, BASE_Y - 50.0, (SHELL_Z0 + SHELL_Z1) / 2)
             * Box(300, 100, SHELL_LEN + 20, align=Align.CENTER))   # flat bed face
    # lightening pockets between chambers, outboard of the channels
    for zc in (32.0, 48.0, 64.0, 80.0):
        for sx in (-1, 1):
            body -= (Pos(sx * 26.0, 6.0, zc)
                     * Box(12.0, 26.0, 8.0, align=Align.CENTER))
    # Skirt vents.  The foot plate top (y = -30), the body cylinder and each
    # skirt web close a lens-shaped pocket x = 18.41..28, y = -30..-21.33 that
    # runs the full 105 mm length: a sealed internal void (check_mesh read the
    # shell as 3 connected shells).  Five windows per web open it to air, so the
    # slicer sees one enclosed volume and the skirt still ties the foot to the
    # body.  Verified by re-running check_mesh: 1 shell.
    for zc in (20.0, 40.0, 60.0, 80.0, 100.0):
        for sx in (-1, 1):
            body -= (Pos(sx * 30.0, -25.6, zc)
                     * Box(8.0, 6.0, 12.0, align=Align.CENTER))
    return body


def print_shell():
    """Standing as used, chimneys vertical, bed datum at Z = 0."""
    return Pos(0, 0, -BASE_Y) * TO_ASM * build_shell()


def asm_shell():
    return TO_ASM * build_shell()


# ---------------------------------------------------------------------------
# 13. slug_01 (the driver) and pin_r1..pin_r8 (the ladder)
# ---------------------------------------------------------------------------
def build_slug():
    """Local +Z = the chamber axis, nose face at z = 0 (also the bed face)."""
    s = Cylinder(SLUG_NOSE_D / 2, SLUG_NOSE_L, align=(Align.CENTER, Align.CENTER, Align.MIN))
    s += Pos(0, 0, SLUG_NOSE_L) * Cylinder(SLUG_FLANGE_D / 2, SLUG_FLANGE_L,
                                           align=(Align.CENTER, Align.CENTER, Align.MIN))
    s += Pos(0, 0, SLUG_NOSE_L + SLUG_FLANGE_L) * Cylinder(
        SLUG_STEM_D / 2, SLUG_STEM_L, align=(Align.CENTER, Align.CENTER, Align.MIN))
    s += Pos(0, 0, SLUG_LEN - SLUG_HEAD_L) * Cylinder(
        SLUG_HEAD_D / 2, SLUG_HEAD_L, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return s


def print_slug():
    return build_slug()


def build_pin(rung: int):
    """pin_r<rung>: D6.20 x height, rung numeral 0.35 deep on the side, twice."""
    h = PIN_HEIGHTS[rung - 1]
    p = Cylinder(PIN_D / 2, h, align=(Align.CENTER, Align.CENTER, Align.MIN))
    size = min(2.6, h - 0.8)
    for sy in (-1, 1):
        pl = Plane(origin=(0, sy * PIN_D / 2, h / 2),
                   x_dir=(sy, 0, 0), z_dir=(0, sy, 0))
        p -= extrude(pl * Text(str(rung), font_size=size,
                               align=(Align.CENTER, Align.CENTER)), -0.35)
    # A glyph like "3" leaves an island in its own crook: a 0.3 mm speck that
    # would print as a floating fleck.  Keep the pin body only.
    solids = p.solids()
    if len(solids) > 1:
        p = max(solids, key=lambda s: s.volume)
    return p


def print_pin(rung: int):
    return build_pin(rung)


# ---------------------------------------------------------------------------
# 14. key_01 — the guess, made physical and public
# ---------------------------------------------------------------------------
LANE_X = (-6.4, -3.2, 0.0, 3.2, 6.4)
# The blade is built tip-first (tip at z = 0) but the brief measures the
# chambers from the plug's front face, and C11 fixes the blade shoulder there.
# So lifter i lives at BLADE_LEN - CHAMBER_X[i]; inserted, it lands on bore i.
KEY_LIFTER_Z = tuple(BLADE_LEN - x for x in CHAMBER_X)
LANE_W = 2.00
# Five lanes at 3.20 pitch inside a 17.40 blade leave 3.48 mm per lane for the
# slot *and* its walls.  At LANE_W 2.80 the slots (2.80 + 2 x 0.30 gap = 3.40)
# overlapped: the blade became one 16.2 mm void with 0.6 mm outer walls, which is
# under one 0.4 nozzle bead of structure on the part that carries the turning
# torque.  2.00 gives 0.60 webs between lanes and 1.00 outer walls.
BAR_SPINE = (2.0, 5.0)                # blade-local y band of every slider spine
LAND_Z = 1.80                         # only one land can be under a D6.20 pin
ROD_CRANK_Y = 21.5                    # corridor ceiling.  Every rod's arm swings
                                      # 8.4 in y under it and the cranks cross lanes
                                      # just below it, so the ceiling has to clear
                                      # the highest arm (land 1 + arm + two print
                                      # gaps = 18.4) with the crank band on top.
PIP = cadfits.print_in_place_gap("sliding", layer_height=0.20, material="PLA")
assert LANE_X[1] - LANE_X[0] - (LANE_W + 2 * PIP["xy"]) >= 0.55       # lane web
assert (BLADE_W - (LANE_X[-1] - LANE_X[0]) - (LANE_W + 2 * PIP["xy"])) / 2 >= 0.95
BOW_L, BOW_W, BOW_H = 46.0, 40.0, 26.0
KEY_LEN = BLADE_LEN + BOW_L           # 142.0


Z_FOOT = 104.0                      # every rod foot rides its staircase here,
                                      # in the bow, so a 28 mm staircase never has
                                      # to fit in front of chamber 1 (z = 24)
ROD_T = 3.00                          # rod thickness along z
ROD_ARM_H = 3.00


def _land_y(setting: int) -> float:
    """Blade-local y of the land that gives slider ``setting``."""
    return BAR_SPINE[1] + 1.0 + LIFTER_H[setting - 1] - LIFTER_H[-1]


ROD_LEN = (BLADE_H + LIFTER_H[0]) - _land_y(1)      # foot underside -> head top


def _bar_origin(setting: int) -> float:
    """Blade-local z of the bar's front end when it is set to ``setting``.

    The staircase runs *tall-at-the-back*: land ``s`` sits at
    ``o + PITCH * (RUNGS - s)``, so the land under the rod foot (always z =
    Z_FOOT) is the tallest one the rod ever meets and every land in front of the
    foot is at least one rung lower.  The rod's arm can then run flat at foot
    height the whole way to its chamber.  The other ordering — the brief's
    natural 1-at-the-front — puts lands up to 8.4 mm *above* the foot under that
    arm, which is what the ARM_Y riser was trying and failing to jump.
    """
    return Z_FOOT - SLIDER_PITCH * (RUNGS - setting)


BAR_Z0 = min(_bar_origin(s) for s in range(1, RUNGS + 1))    # 76.0, front-most land
BAR_TAB_DZ = 33.0                     # thumb tab, bar-local; stays in the bow slot,
                                      # and clear of the rod arm's rear end
assert BAR_Z0 + BAR_TAB_DZ > BLADE_LEN + 6.0
assert _bar_origin(RUNGS) + BAR_TAB_DZ + 2.5 <= BLADE_LEN + BOW_L


def _slider_bar(i: int, setting: int = 1, seated: bool = False):
    """One stepped slider: 8 flat lands, 4.00 pitch, 28.0 travel, plus a thumb
    tab that reads against the lane numerals engraved on the bow.

    ``seated`` = resting on the corridor floor, which is where it lives in play
    and where every land height in §4 is measured.  Unseated is the printed
    pose: lifted one print-in-place gap so the slicer bridges under it instead
    of welding it to the floor.
    """
    x, o = LANE_X[i], _bar_origin(setting)
    dy = 0.0 if seated else PIP["z"]
    bar = (Pos(x, (BAR_SPINE[0] + BAR_SPINE[1]) / 2 + dy, o + 17.0)
           * Box(LANE_W, BAR_SPINE[1] - BAR_SPINE[0], 40.0, align=Align.CENTER))
    for s in range(1, RUNGS + 1):
        bar += (Pos(x, (BAR_SPINE[1] + _land_y(s)) / 2 + dy,
                    o + SLIDER_PITCH * (RUNGS - s))
                * Box(LANE_W, _land_y(s) - BAR_SPINE[1], 3.0, align=Align.CENTER))
    bar += (Pos(x, (BAR_SPINE[1] + BOW_H - 1.0) / 2 + dy, o + BAR_TAB_DZ)
            * Box(LANE_W, BOW_H - 1.0 - BAR_SPINE[1], 5.0, align=Align.CENTER))
    return bar


def _lifter_rod(i: int, setting: int, seated: bool = False):
    """L-shaped: foot on the staircase in the bow, arm back to the chamber,
    cranked post to the centreline, D4.80 head through the plug's aperture.

    Unseated the rod stands two gaps high — one because its bar is lifted off
    the floor, one because it is lifted off its bar.  Both close on the first
    drop, which is why every height in §4 is quoted seated.
    """
    x, zc = LANE_X[i], KEY_LIFTER_Z[i]
    y0 = _land_y(setting) + (0.0 if seated else 2 * PIP["z"])
    w = LANE_W - 2 * PIP["xy"]
    # foot and arm are one flat bar at land height: nothing in front of the foot
    # is ever taller than the land the foot is on (see _bar_origin).
    z_rear = Z_FOOT + 1.5                      # 1.0 clear of the thumb tab at set 1
    rod = (Pos(x, y0 + ROD_ARM_H / 2, (zc + z_rear) / 2)
           * Box(w, ROD_ARM_H, z_rear - zc, align=Align.CENTER))
    rod += (Pos(x, (y0 + ROD_CRANK_Y) / 2, zc)
            * Box(w, ROD_CRANK_Y - y0, ROD_T, align=Align.CENTER))         # post
    if x:
        rod += (Pos(x / 2, ROD_CRANK_Y - 1.0, zc)
                * Box(abs(x) + w, 2.0, ROD_T, align=Align.CENTER))         # crank
    rod += (Rot(-90, 0, 0) * Pos(0, -zc, ROD_CRANK_Y - 2.0)
            * Cylinder(LIFTER_D / 2, y0 + ROD_LEN - ROD_CRANK_Y + 2.0,
                       align=(Align.CENTER, Align.CENTER, Align.MIN)))
    return rod


def build_key(settings=(1, 2, 3, 4, 5), seated: bool = False):
    """key_01: frame + 5 print-in-place stepped sliders + 5 print-in-place rods.

    Blade-local frame: tip at z = 0, blade bottom at y = 0, centreline x = 0.
    The brief specifies print-in-place rods, so this file is deliberately a
    compound of 11 bodies rather than one solid.
    """
    frame = (Pos(0, BLADE_H / 2, BLADE_LEN / 2)
             * Box(BLADE_W, BLADE_H, BLADE_LEN, align=Align.CENTER))
    frame += (Pos(0, BOW_H / 2, BLADE_LEN + BOW_L / 2)
              * Box(BOW_W, BOW_H, BOW_L, align=Align.CENTER))
    frame += (Pos(0, (BLADE_H + 6.0) / 2, BLADE_LEN + 1.5)
              * Box(BOW_W, BLADE_H + 6.0, 3.0, align=Align.CENTER))     # shoulder stop
    g = PIP["xy"]
    for i, x in enumerate(LANE_X):
        # staircase + arm corridor, one lane wide, from the front face of this
        # lane's post (which is ROD_T thick about its chamber) to the bow end.
        zlo = min(BAR_Z0 - 5.0, KEY_LIFTER_Z[i] - ROD_T / 2 - g)
        frame -= (Pos(x, (BAR_SPINE[0] + ROD_CRANK_Y) / 2, (zlo + KEY_LEN) / 2)
                  * Box(LANE_W + 2 * g, ROD_CRANK_Y - BAR_SPINE[0],
                        KEY_LEN - zlo, align=Align.CENTER))
        # thumb slot through the bow roof
        frame -= (Pos(x, (ROD_CRANK_Y + BOW_H) / 2, (BLADE_LEN + 4.0 + KEY_LEN) / 2)
                  * Box(LANE_W + 2 * g, BOW_H - ROD_CRANK_Y,
                        KEY_LEN - BLADE_LEN - 4.0, align=Align.CENTER))
        # crank slot + D5.40 roof guide at the chamber.  The slot has to hold the
        # crank (lane x -> centreline) *and* the D4.80 head at x = 0, so it spans
        # from whichever of the two reaches further out on each side.
        cx0 = min(x - LANE_W / 2 - g, -(LIFTER_D / 2 + g + 0.2))
        cx1 = max(x + LANE_W / 2 + g, +(LIFTER_D / 2 + g + 0.2))
        frame -= (Pos((cx0 + cx1) / 2, (ROD_CRANK_Y - 3.0 + BLADE_H + 1.0) / 2,
                      KEY_LIFTER_Z[i])
                  * Box(cx1 - cx0, BLADE_H + 4.0 - ROD_CRANK_Y,
                        ROD_T + 2 * g, align=Align.CENTER))
        frame -= (Rot(-90, 0, 0) * Pos(0, -KEY_LIFTER_Z[i], ROD_CRANK_Y)
                  * Cylinder(LIFTER_D / 2 + g, BLADE_H,
                             align=(Align.CENTER, Align.CENTER, Align.MIN)))
        # 8 witness grooves in the corridor floor, 4.00 pitch: the bar's front
        # edge reads against them.  [DEV] not a sprung click - see DEVIATIONS.
        for s in range(1, RUNGS + 1):
            frame -= (Pos(x, BAR_SPINE[0], _bar_origin(s))
                      * Box(LANE_W, 0.8, 1.2, align=Align.CENTER))
        # lane numerals 1-8 on the bow roof beside the thumb tab, readable
        # across the table
        pl = Plane(origin=(0, BOW_H, 0), x_dir=(1, 0, 0), z_dir=(0, 1, 0))
        for s in range(1, RUNGS + 1):
            frame -= extrude(pl * Pos(x + LANE_W / 2 + 1.7,
                                      -(_bar_origin(s) + BAR_TAB_DZ), 0)
                             * Text(str(s), font_size=2.6,
                                    align=(Align.CENTER, Align.CENTER)), -0.5)
    return (frame,
            [_slider_bar(i, settings[i], seated) for i in range(N_CHAMBERS)],
            [_lifter_rod(i, settings[i], seated) for i in range(N_CHAMBERS)])


def key_shape(settings=(1, 2, 3, 4, 5), seated: bool = False):
    """The whole key in the blade-local frame, as one compound of 11 bodies."""
    frame, bars, rods = build_key(settings, seated)
    out = frame
    for b in bars + rods:
        out += b
    return out


def print_key(settings=(RUNGS,) * N_CHAMBERS, seated: bool = False):
    """Blade flat (brief §3): blade-local +Y becomes the print Z, so every land
    is a horizontal face set by a layer count and the print-in-place gaps are
    vertical.  Printed with every slider at 8, the setting whose lifters stand
    lowest, so the plate height is the bow and not a raised lifter."""
    return bed(Rot(90, 0, 0) * key_shape(settings, seated))


# ---------------------------------------------------------------------------
# 15. Shared helpers for the rest of the bill
# ---------------------------------------------------------------------------
def bed(shape):
    """Drop a shape onto the bed: min Z = 0, centred in XY."""
    bb = shape.bounding_box()
    return Pos(-(bb.min.X + bb.max.X) / 2,
               -(bb.min.Y + bb.max.Y) / 2, -bb.min.Z) * shape


def _prism_zy(pts, x0, x1):
    """Prism whose (z, y) profile is ``pts``, extruded along X from x0 to x1."""
    p3 = [(0.0, y, z) for z, y in list(pts) + [pts[0]]]
    face = make_face(Polyline(*p3))
    return Pos(x0, 0, 0) * extrude(face, x1 - x0, dir=(1, 0, 0))


def _socket_grid(cols, rows, pitch_x, pitch_y, dia, depth, z_top,
                 labels=None, label_dy=0.0, label_size=3.0):
    """Cutting solid: cols x rows blind sockets, plus optional column numerals."""
    cut = None
    for i in range(cols):
        x = (i - (cols - 1) / 2) * pitch_x
        for j in range(rows):
            y = (j - (rows - 1) / 2) * pitch_y
            s = (Pos(x, y, z_top - depth)
                 * Cylinder(dia / 2, depth + 0.1,
                            align=(Align.CENTER, Align.CENTER, Align.MIN)))
            cut = s if cut is None else cut + s
        if labels:
            cut += engrave(labels[i], label_size, 0.5, Plane.XY.offset(z_top),
                           Pos(x, label_dy, 0))
    return cut


# ---------------------------------------------------------------------------
# 16. cap_01 — captures the plug axially
# ---------------------------------------------------------------------------
def build_cap():
    """Shell-local frame: +Z = plug axis.  Plate face against the shell's rear
    face at SHELL_Z1, three snap tabs reaching back into the shell."""
    c = (Pos(0, 0, SHELL_Z1)
         * Cylinder(CAP_OD / 2, CAP_PLATE_T, align=(Align.CENTER, Align.CENTER, Align.MIN)))
    r_in = CAP_TAB_R - CAP_TAB[1] / 2
    r_out = CAP_TAB_R + CAP_TAB[1] / 2
    for k in range(3):
        phi = 120.0 * k
        tab = (Rot(0, 0, phi) * Pos(0, (r_in + r_out) / 2, SHELL_Z1 - CAP_TAB_L)
               * Box(CAP_TAB[0], r_out - r_in, CAP_TAB_L,
                     align=(Align.CENTER, Align.CENTER, Align.MIN)))
        nib = Rot(0, 0, phi) * _prism_zy(
            [(SHELL_Z1 - CAP_NIB_Z[1], r_out),
             (SHELL_Z1 - CAP_NIB_Z[0], r_out + CAP_ENGAGE),
             (SHELL_Z1 - CAP_NIB_Z[0], r_out)],
            -CAP_TAB[0] / 2, CAP_TAB[0] / 2)
        c += tab + nib
    # D45.80 spigot recess: locates on the plug's rear journal and sets the end float
    c -= (Pos(0, 0, SHELL_Z1)
          * Cylinder(CAP_BORE_D / 2, CAP_SPIGOT_DEPTH,
                     align=(Align.CENTER, Align.CENTER, Align.MIN)))
    c -= (Pos(0, 0, SHELL_Z1 - 1)
          * Cylinder(CAP_SIGHT_D / 2, CAP_PLATE_T + 2,
                     align=(Align.CENTER, Align.CENTER, Align.MIN)))
    return c


def print_cap():
    """Plate on the bed, tabs up: no support, the nib ledges bridge 1.2."""
    return bed(Rot(0, 180, 0) * build_cap())


def asm_cap():
    return TO_ASM * build_cap()


# ---------------------------------------------------------------------------
# 17. hood_01 — the hidden state
# ---------------------------------------------------------------------------
def build_hood():
    """Shell-local.  Roof + the +X wall + both end walls; open downward and on
    the -X (Locksmith) face.  Printed standing on that open face, so every wall
    is a vertical plane and nothing bridges."""
    hw, hl = HOOD_SEAT
    zc = (SHELL_Z0 + SHELL_Z1) / 2
    x_out = hw / 2 + HOOD_WALL / 2                  # +34.45
    x_in = -x_out                                    # open-face edge
    z0, z1 = zc - hl / 2 - HOOD_WALL / 2, zc + hl / 2 + HOOD_WALL / 2
    y0, y1 = HOOD_SEAT_Y, HOOD_CEIL_Y

    h = (Pos((x_in + x_out) / 2, (y1 + y1 + HOOD_WALL) / 2, (z0 + z1) / 2)
         * Box(x_out - x_in, HOOD_WALL, z1 - z0, align=Align.CENTER))          # roof
    h += (Pos(x_out - HOOD_WALL / 2, (y0 + y1) / 2, (z0 + z1) / 2)
          * Box(HOOD_WALL, y1 - y0, z1 - z0, align=Align.CENTER))              # +X wall
    for z in (z0 + HOOD_WALL / 2, z1 - HOOD_WALL / 2):
        h += (Pos((x_in + x_out) / 2, (y0 + y1) / 2, z)
              * Box(x_out - x_in, y1 - y0, HOOD_WALL, align=Align.CENTER))     # ends
    # finger lip on the open edge, so it lifts one-handed
    h += (Pos(x_in + 3.0, y1 + HOOD_WALL / 2, (z0 + z1) / 2)
          * Box(6.0, HOOD_WALL, z1 - z0, align=Align.CENTER))
    return h


def print_hood():
    return bed(Rot(0, 90, 0) * build_hood())


def asm_hood(lift: float = 0.0):
    return TO_ASM * Pos(0, lift, 0) * build_hood()


# ---------------------------------------------------------------------------
# 18. latch_01 — the click
# ---------------------------------------------------------------------------
def build_latch():
    """Shell-local.  Root pressed into the seat at the front, 1.80 x 24.0
    flexure, nose through the shell window onto the plug's latch cam."""
    s_ = LATCH_SEAT
    x_seat0, x_seat1 = s_["x0"], s_["x1"]
    # Slide-fit root plus four short press pads: same 0.10 interference the brief
    # asks for, a twentieth of the insertion force and a twentieth of the
    # modelled overlap.
    root = (Pos((x_seat0 + x_seat1) / 2, (s_["y0"] + s_["y1"]) / 2,
                (LATCH_ROOT_Z[0] + LATCH_ROOT_Z[1]) / 2)
            * Box(x_seat1 - x_seat0 - LATCH_PRESS,
                  s_["y1"] - s_["y0"] - LATCH_PRESS,
                  LATCH_ROOT_Z[1] - LATCH_ROOT_Z[0], align=Align.CENTER))
    for sx in (-1, 1):
        for zp in (LATCH_ROOT_Z[0] + 6.0, LATCH_ROOT_Z[1] - 6.0):
            xp = (x_seat0 if sx < 0 else x_seat1) - sx * LATCH_PRESS / 2
            root += (Pos(xp, (s_["y0"] + s_["y1"]) / 2, zp)
                     * Box(LATCH_PRESS * 2, 8.0, 6.0, align=Align.CENTER))
    t = LATCH_FLEX[0]
    flex = (Pos(x_seat1 - t / 2, 0.0, (LATCH_FLEX_Z[0] + LATCH_FLEX_Z[1]) / 2)
            * Box(t, 10.0, LATCH_FLEX_Z[1] - LATCH_FLEX_Z[0], align=Align.CENTER))
    nose = (Pos((x_seat1 - t + LATCH_NOSE_X) / 2, 0.0,
                (LATCH_NOSE_Z[0] + LATCH_NOSE_Z[1]) / 2)
            * Box(LATCH_NOSE_X - (x_seat1 - t), 8.0,
                  LATCH_NOSE_Z[1] - LATCH_NOSE_Z[0], align=Align.CENTER))
    nib = (Pos((LATCH_NOSE_X + LATCH_NIB_X) / 2, 0.0, (CAM_Z[0] + CAM_Z[1]) / 2)
           * Box(LATCH_NIB_X - LATCH_NOSE_X, LATCH_NIB[0], CAM_Z[1] - CAM_Z[0],
                 align=Align.CENTER))
    body = root + flex + nose + nib
    # 30 deg cam-follower face on the +Y corner of the nose: the plug's surface
    # sweeps past in -Y, so this is the edge the rising cam meets first.
    body -= (Pos(LATCH_NOSE_X, 4.0 - LATCH_RAMP_Y, (LATCH_NOSE_Z[0] + LATCH_NOSE_Z[1]) / 2)
             * Rot(0, 0, 120.0)
             * Box(12.0, 12.0, LATCH_NOSE_Z[1] - LATCH_NOSE_Z[0] + 2,
                   align=(Align.MIN, Align.MAX, Align.CENTER)))
    return body


def print_latch():
    """Flexure bending in the print plane: the shell-local X (its 9.0) becomes
    the print Z."""
    return bed(Rot(0, -90, 0) * build_latch())


def asm_latch():
    return TO_ASM * build_latch()


# ---------------------------------------------------------------------------
# 19. lever_01 — the reset slide, and the lid over the chimney row
# ---------------------------------------------------------------------------
def _lever_shelf(zc: float):
    """One period of the lift shelf, as two ledges either side of the stem slot.

    Profile, measured back from the chamber: nothing for the first LEVER_RAMP[0]
    (so a low driver stays low at RUN), then a ramp up to LEVER_TOP_Y, then a
    short land the head rests on at RESET.
    """
    a, b = LEVER_RAMP
    pts = [(zc - b - LEVER_LAND, LEVER_Y0), (zc - b - LEVER_LAND, LEVER_TOP_Y),
           (zc - b, LEVER_TOP_Y), (zc - a, LEVER_RAMP_Y0), (zc - a, LEVER_Y0)]
    x0, x1 = LEVER_LEDGE_X
    return (_prism_zy(pts, x0, x1) + _prism_zy(pts, -x1, -x0))


def build_lever(travel: float = 0.0):
    """Shell-local, at slide position ``travel`` (0 = RUN, LEVER_DETENTS[1] =
    LOAD/RESET).  Body between the shell rails, male dovetails into them."""
    z0, z1 = LEVER_Z0, LEVER_Z0 + LEVER_L
    body = (Pos(0, (LEVER_Y0 + LEVER_Y1) / 2, (z0 + z1) / 2)
            * Box(2 * 12.85, LEVER_Y1 - LEVER_Y0, z1 - z0, align=Align.CENTER))
    tongue = [(12.0, 50.5), (17.0, 48.0), (17.0, 56.0), (12.0, 53.5)]
    for sx in (-1, 1):
        body += _prism_xy([(sx * px, py) for px, py in tongue], z0, z1)
    # head tunnel + stem slot, the full length, so the lever can slide with the
    # drivers in place; roofed so no driver height leaks (brief §6)
    body -= (Pos(0, (LEVER_Y0 + LEVER_ROOF_Y) / 2, (z0 + z1) / 2)
             * Box(LEVER_TUNNEL_W, LEVER_ROOF_Y - LEVER_Y0, z1 - z0, align=Align.CENTER))
    for zc in CHAMBER_X:
        body += _lever_shelf(zc)
        # loading hole: over the chimney at LOAD/RESET only
        body -= (Pos(0, LEVER_ROOF_Y, zc - LEVER_DETENTS[1])
                 * Cylinder(LEVER_LOAD_D / 2, LEVER_Y1 - LEVER_ROOF_Y + 1,
                            align=(Align.CENTER, Align.CENTER, Align.MIN)))
    # detent dimples on both flanks, one per position
    for sx in (-1, 1):
        for t in LEVER_DETENTS:
            body -= (Pos(sx * 12.85, 47.0, LEVER_DETENT_NIB_Z - t)
                     * Box(0.8, 1.2, 2.6, align=Align.CENTER))
    lab_plane = Plane(origin=(0, LEVER_Y1, 0), x_dir=(0, 0, 1), z_dir=(0, 1, 0))
    for t, label in zip(LEVER_DETENTS, ("RUN", "LOAD")):
        body -= engrave(label, 4.0, 0.5, lab_plane,
                        Pos(0, 0, LEVER_DETENT_NIB_Z - t))
    return Pos(0, 0, travel) * body


def print_lever():
    return bed(TO_ASM * build_lever())


def asm_lever(travel: float = 0.0):
    return TO_ASM * build_lever(travel)


# ---------------------------------------------------------------------------
# 20. Stock, record and marker parts
# ---------------------------------------------------------------------------
CASE_WALL = 3.0
CASE_TUBE_PITCH = (11.0, 10.0)        # 8 rungs across x, 5 sockets deep in y
CASE_FLOOR = 2.0
CASE_LID_T = 2.0
CASE_LID_FIT = 0.15
TRAY_PITCH = (13.0, 6.4)
TRAY_SOCKET_DEPTH = 6.0
BOARD_TIME = (12, 10.0)               # holes, pitch
BOARD_LANE = (21, 6.0)
BOARD_HOLE_DEPTH = 4.0


def build_case():
    """case_01: 8 columns of 5 tubes, one column per rung, and a sliding lid.
    Local +Z up, floor at z = 0."""
    c = Box(CASE_L, CASE_W, CASE_T - 3.0,
            align=(Align.CENTER, Align.CENTER, Align.MIN))
    z_top = CASE_T - 3.0
    c -= _socket_grid(RUNGS, 5, CASE_TUBE_PITCH[0], CASE_TUBE_PITCH[1],
                      TUBE_D, TUBE_DEPTH, z_top,
                      labels=[str(r) for r in range(1, RUNGS + 1)],
                      label_dy=CASE_W / 2 - 4.0, label_size=4.0)
    # lid rails: 2.0 slot with a 1.0 lip, open at the +X end
    for sy in (-1, 1):
        c += (Pos(0, sy * (CASE_W / 2 - 1.0), z_top)
              * Box(CASE_L, 2.0, 3.0, align=(Align.CENTER, Align.CENTER, Align.MIN)))
        c += (Pos(0, sy * (CASE_W / 2 - 4.0), z_top + CASE_LID_T + CASE_LID_FIT)
              * Box(CASE_L, 6.0, 3.0 - CASE_LID_T - CASE_LID_FIT,
                    align=(Align.CENTER, Align.CENTER, Align.MIN)))
    c += (Pos(-CASE_L / 2 + 1.0, 0, z_top)
          * Box(2.0, CASE_W, 3.0, align=(Align.CENTER, Align.CENTER, Align.MIN)))
    return c


def print_case():
    return bed(build_case())


def build_lid():
    w = CASE_W - 4.0 - 2 * CASE_LID_FIT
    lid = Box(CASE_L - 5.0, w, CASE_LID_T,
              align=(Align.CENTER, Align.CENTER, Align.MIN))
    lid -= engrave("RE-PIN  PINS 1-8", 6.0, 0.5, Plane.XY.offset(CASE_LID_T),
                   Pos(0, 0, 0))
    return lid


def print_lid():
    return bed(build_lid())


def build_tray():
    """tray_01: the public record of the round's five starting rungs."""
    t = Box(TRAY_L, TRAY_W, TRAY_T, align=(Align.CENTER, Align.CENTER, Align.MIN))
    t -= _socket_grid(RUNGS, 5, TRAY_PITCH[0], TRAY_PITCH[1], SOCKET_D,
                      TRAY_SOCKET_DEPTH, TRAY_T,
                      labels=[str(r) for r in range(1, RUNGS + 1)],
                      label_dy=TRAY_W / 2 - 3.5, label_size=3.4)
    return t


def print_tray():
    return bed(build_tray())


def build_board():
    """board_01: the time rail (12 -> 1) and the Locksmith lane (0 -> 20)."""
    b = Box(BOARD_L, BOARD_W, BOARD_T, align=(Align.CENTER, Align.CENTER, Align.MIN))
    n, pitch = BOARD_TIME
    for i in range(n):
        x = (i - (n - 1) / 2) * pitch
        b -= (Pos(x, BOARD_W / 2 - 9.0, BOARD_T - BOARD_HOLE_DEPTH)
              * Cylinder(SOCKET_D / 2, BOARD_HOLE_DEPTH + 0.1,
                         align=(Align.CENTER, Align.CENTER, Align.MIN)))
        b -= engrave(str(n - i), 3.2, 0.5, Plane.XY.offset(BOARD_T),
                     Pos(x, BOARD_W / 2 - 3.0, 0))
    n, pitch = BOARD_LANE
    for i in range(n):
        x = (i - (n - 1) / 2) * pitch
        b -= (Pos(x, -BOARD_W / 2 + 9.0, BOARD_T - BOARD_HOLE_DEPTH)
              * Cylinder(SOCKET_D / 2, BOARD_HOLE_DEPTH + 0.1,
                         align=(Align.CENTER, Align.CENTER, Align.MIN)))
        if i % 5 == 0:
            b -= engrave(str(i), 3.2, 0.5, Plane.XY.offset(BOARD_T),
                         Pos(x, -BOARD_W / 2 + 3.0, 0))
    return b


def print_board():
    return bed(build_board())


def build_peg():
    p = Cylinder(PEG_D / 2, PEG_L - 2.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    p += Pos(0, 0, PEG_L - 2.0) * Cylinder(
        3.6, 2.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return p


def print_peg():
    return bed(build_peg())


# ---------------------------------------------------------------------------
# 21. Assembly placements
# ---------------------------------------------------------------------------
def asm_pin(i: int, rung: int, setting: int):
    """Pin in chamber ``i`` (0-based), sitting on the lifter for ``setting``."""
    r0 = LIFTER_TOP_Y[setting - 1]
    return (TO_ASM * Pos(0, 0, CHAMBER_X[i]) * Rot(-90, 0, 0)
            * Pos(0, 0, r0) * build_pin(rung))


def asm_slug(i: int, rung: int, setting: int):
    nose = LIFTER_TOP_Y[setting - 1] + PIN_HEIGHTS[rung - 1]
    return (TO_ASM * Pos(0, 0, CHAMBER_X[i]) * Rot(-90, 0, 0)
            * Pos(0, 0, nose) * build_slug())


def asm_key(settings=(1, 2, 3, 4, 5)):
    """Key fully home: shoulder on the plug's front face, blade on the keyway
    floor.  The blade is built tip-first, so it goes in mirrored about z."""
    return (TO_ASM * Pos(0, KEYWAY_FLOOR_Y, BLADE_LEN) * Rot(0, 180, 0)
            * key_shape(settings, seated=True))


# ---------------------------------------------------------------------------
# 22. GP1 — the golden part (brief §8): one chamber, printed before anything else
# ---------------------------------------------------------------------------
GP1_LEN = 60.0
GP1_ZC = 30.0
GP1_STOP = 36.0


def build_gp1_plug():
    """Stub plug: 60 long, D44, one chamber, one 36 deg gate notch, keyway."""
    p = Cylinder(R_PLUG, GP1_LEN, align=(Align.CENTER, Align.CENTER, Align.MIN))
    p += Pos(0, 0, 0) * Cylinder(JOURNAL_R, 8.0,
                                 align=(Align.CENTER, Align.CENTER, Align.MIN))
    p += Pos(0, 0, GP1_LEN - 8.0) * Cylinder(
        JOURNAL_R, 8.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    p -= (Pos(0, (KEYWAY_ROOF_Y + KEYWAY_FLOOR_Y) / 2, GP1_LEN / 2)
          * Box(KEYWAY_W, KEYWAY_H, GP1_LEN + 2, align=Align.CENTER))
    p -= _chamber_bore(GP1_ZC)
    p -= _gate_notch(GP1_ZC, GP1_STOP)
    return p


def print_gp1_plug():
    return bed(build_gp1_plug())


def build_gp1_shell():
    """Stub shell: cradle + one chimney with the shoulder datum + one 36 deg
    arc channel, on a foot, printed standing exactly as shell_01 is."""
    b = (Pos(0, 0, 0) * Cylinder(BODY_OUTER_R, GP1_LEN,
                                 align=(Align.CENTER, Align.CENTER, Align.MIN)))
    b += (Pos(0, (DECK_Y0 + DECK_TOP_Y) / 2, GP1_LEN / 2)
          * Box(2 * DECK_HALF_W, DECK_TOP_Y - DECK_Y0, GP1_LEN - 8.0,
                align=Align.CENTER))
    b += (Pos(0, BASE_Y + FOOT_T / 2, GP1_LEN / 2)
          * Box(2 * SHELL_HALF_W, FOOT_T, GP1_LEN, align=Align.CENTER))
    for sx in (-1, 1):
        b += (Pos(sx * 30.0, -19.0, GP1_LEN / 2)
              * Box(4.0, 30.0, GP1_LEN, align=Align.CENTER))
    b -= (Pos(0, 0, -1) * Cylinder(R_BORE, GP1_LEN + 2,
                                   align=(Align.CENTER, Align.CENTER, Align.MIN)))
    b -= _chimney_cut(GP1_ZC, GP1_STOP)
    b -= (Pos(0, BASE_Y - 50.0, GP1_LEN / 2)
          * Box(300, 100, GP1_LEN + 20, align=Align.CENTER))
    return b


def print_gp1_shell():
    return bed(Pos(0, 0, -BASE_Y) * TO_ASM * build_gp1_shell())
