#!/usr/bin/env python
"""Metes and Bounds -- parametric print kit (CadQuery).

Source of truth: ../brief.md v1.0.  Every number below is that brief's number
unless a comment says otherwise; the handful of deviations are all flagged with
`DEVIATION:` and are geometric corrections, not taste.

The signature part is `folding_rule_10seg`: a ten-segment planar folding rule
with nine PRINT-IN-PLACE knuckle hinges.  Each knuckle is a real mechanism --
a captured pivot post, two 0.60 mm compliant detent arms riding a notched
barrel, and radial hard-stop faces -- not a decorative bump.  It is modelled
in the play frame (board face at z = 0, top face at z = 12) and emitted in the
brief's print orientation (top face on the bed, pegs up).

Run:  /Users/d/.cadcode-venv/bin/python cad/build_parts.py
"""

from __future__ import annotations

import json
import math
import struct
import time
from pathlib import Path

import cadquery as cq

# --------------------------------------------------------------------------
# paths
# --------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build"
OUT.mkdir(parents=True, exist_ok=True)

BED = 246.0  # usable X/Y envelope (mm)
FONT = "Arial"

# --------------------------------------------------------------------------
# master constants (brief S1.2 / S2)
# --------------------------------------------------------------------------
P = 36.000  # node pitch -- governs everything

SEG_W = 12.00  # segment body cross-section width
SEG_H = 12.00  # rule height, board face -> top face
PUCK_R = 9.00  # knuckle puck outside radius (D18)
BODY_R = 10.00  # segment body starts at r = 10 from each axis
CAP_R = 7.00  # root / tip end cap D14

# knuckle Z stack, PLAY frame (z = 0 is the board face, z = 12 the top face).
# brief S1.3 gives it print-side-up; play_z = 12 - print_z.
Z_TOP = 12.00
Z_TOPEAR_BOT = 9.00  # top ear   : 9.00 -> 12.00   (owner: seg N)
Z_BARREL_TOP = 8.80  # 0.20 clearance gap
Z_NOTCH_TOP = 8.80  # notch sub-band: 5.80 -> 8.80 (detent arms live here)
Z_NOTCH_BOT = 5.80
Z_NECK_TOP = 5.60  # 0.20 sub-band clearance
Z_NECK_BOT = 3.00  # neck sub-band : 3.00 -> 5.60
Z_BARREL_BOT = 3.00
Z_BOTEAR_TOP = 2.80  # 0.20 clearance gap
Z_BOTEAR_BOT = 0.00  # bottom ear: 0.00 -> 2.80   (owner: seg N)

BARREL_R = 6.50  # barrel OD 13.00
BORE_R = 2.70  # barrel bore D5.40
POST_R = 2.50  # pivot post D5.00 -> 0.20 radial clearance
POST_BOT = 1.60  # post tip
CAPTURE_BOT = 1.40  # blind capture bore floor in the bottom ear (0.20 axial)

SPINE_R_IN = 6.80  # 0.30 clear of the barrel OD
SPINE_HALF_NOTCH = 45.0  # spine span in the notch sub-band
# DEVIATION (brief S1.7): the nominal hard-stop face pair sits at +-67.4 deg,
# which would print the four as-printed L/R knuckles with their stop faces in
# contact -- they would fuse on the bed.  The spine face is pulled back to
# 65.6 deg, so at the detented phi = +-90 deg there is a 1.8 deg printed gap
# (0.21 mm at r 6.80, 0.31 mm at r 10.00) and the mechanical stop lands at
# +-88.2 deg, 1.8 deg past the detent.  The V-detent stays the angular datum,
# exactly as the brief's S6.1 clause 1 already requires.
SPINE_HALF_NECK = 65.6

NECK_W = 5.00  # neck width at the barrel
NECK_R_STEP = 8.70  # reduced section -> full-band section
NECK_HALF = math.degrees(math.asin((NECK_W / 2) / BARREL_R))  # 22.62 deg

ARM_T = 0.60  # the compliant film
ARM_R_ROOT = 8.00  # mean curve radius at the root
ARM_R_TIP = 7.00  # mean curve radius at the tip
ARM_ROOT_A = 81.5  # root angle -> ~7.0 mm free arc length (brief L = 7.00)
ARM_NOSE_A = 135.0  # nose seat angle
NOSE_R = 1.00
NOSE_SEAT_R = 6.50  # nose centre radius, seated
BUTTRESS_R_OUT = 8.30  # rigid arm root backing (clears the neck at r 8.70)

# DEVIATION (brief S1.8): a 60 deg V 1.00 mm deep cannot seat an R1.00 nose --
# tangency puts the nose centre 2.00 mm out from the apex, i.e. at r 7.50,
# which is the riding-the-OD position, so the detent would have ~0 travel.
# The V is deepened to an apex at r 4.10 (2.40 below the OD).  That restores
# the brief's own numbers exactly: nose centre r 6.50 seated, r 7.50 riding,
# 1.00 mm working deflection -- and leaves a 0.20 mm printed flank gap, the
# same clearance every other print-in-place face in this part uses.  (0.15 mm,
# the exact-tangency figure, is below what a 0.30 mm extrusion separates.)
NOTCH_APEX_R = 4.10
NOTCH_HALF_ANGLE = 30.0  # 60 deg included
NOTCH_FLANK_GAP = (6.50 - NOTCH_APEX_R) * math.sin(math.radians(30.0)) - 1.00

PEG_R = 1.50  # hinge/tip peg D3.00
PEG_LEN = 2.50
PEG_LEAD = 1.50  # 60 deg conical lead
ROOT_PEG_R = 2.10  # root peg D4.20, snug in the D4.40 socket
ROOT_PEG_CHAM = 0.50

ENGRAVE = 0.60

# board (brief S2)
BOARD = 236.00
BOARD_PLATE = 5.00
BOARD_RIB = 3.00
BOARD_Z = BOARD_PLATE + BOARD_RIB  # 8.00, play face up at z = 8
BORDER = 10.00
SOCKET_R = 2.20  # D4.40
SOCKET_DEPTH = 3.00
SOCKET_CHAM = 0.60
DIMPLE_R = 3.00  # D6.00
DIMPLE_DEPTH = 1.50
GRID_W = 1.00

# score rail (brief S4)
RAIL_X, RAIL_Y, RAIL_Z = 220.00, 82.00, 6.00
SCORE_HOLE_R = 2.20
ROUND_HOLE_R = 2.70

# as-printed hinge letters, root -> tip (brief S1.10)
AS_PRINTED = "SSLLSSRRS"


# --------------------------------------------------------------------------
# primitive helpers -- everything returns a cq.Workplane
# --------------------------------------------------------------------------
def _vals(p):
    return p.vals() if isinstance(p, cq.Workplane) else [p]


def fuse(parts):
    vs = [v for p in parts for v in _vals(p)]
    return cq.Workplane(obj=vs[0] if len(vs) == 1 else vs[0].fuse(*vs[1:]))


def cut(base, parts):
    vs = [v for p in parts for v in _vals(p)]
    if not vs:
        return base
    return cq.Workplane(obj=base.val().cut(*vs))


def box(x0, x1, y0, y1, z0, z1):
    return (
        cq.Workplane("XY")
        .box(x1 - x0, y1 - y0, z1 - z0, centered=False)
        .translate((x0, y0, z0))
    )


def cyl(r, z0, z1, x=0.0, y=0.0):
    return cq.Workplane(obj=cq.Solid.makeCylinder(r, z1 - z0, cq.Vector(x, y, z0)))


def cone(r0, r1, z0, z1, x=0.0, y=0.0):
    return cq.Workplane(obj=cq.Solid.makeCone(r0, r1, z1 - z0, cq.Vector(x, y, z0)))


def _arc(r, a0, a1, n=None):
    if n is None:
        n = max(3, int(abs(a1 - a0) / 2.5) + 2)
    return [
        (
            r * math.cos(math.radians(a0 + (a1 - a0) * i / (n - 1))),
            r * math.sin(math.radians(a0 + (a1 - a0) * i / (n - 1))),
        )
        for i in range(n)
    ]


def poly(pts, z0, z1):
    return cq.Workplane("XY").polyline(pts).close().extrude(z1 - z0).translate((0, 0, z0))


def sector(r_in, r_out, a0, a1, z0, z1):
    return poly(_arc(r_out, a0, a1) + list(reversed(_arc(r_in, a0, a1))), z0, z1)


def text_cutter(txt, size, depth, x, y, ztop, rot=0.0, halign="center"):
    """A solid to subtract, sinking `depth` below the face at z = ztop."""
    t = cq.Workplane("XY").text(
        txt, size, depth + 0.4, combine=False, font=FONT, halign=halign, valign="center"
    )
    return t.rotate((0, 0, 0), (0, 0, 1), rot).translate((x, y, ztop - depth))


def rot_z(wp, deg):
    return wp.rotate((0, 0, 0), (0, 0, 1), deg)


def to_print(wp):
    """Play frame -> print frame: rotate 180 deg about X, drop min z to 0."""
    wp = wp.rotate((0, 0, 0), (1, 0, 0), 180)
    bb = wp.val().BoundingBox()
    return wp.translate((0, 0, -bb.zmin))


def zero_xy(wp):
    bb = wp.val().BoundingBox()
    return wp.translate((-bb.xmin, -bb.ymin, 0))


# --------------------------------------------------------------------------
# 1. folding_rule_10seg
# --------------------------------------------------------------------------
# Board-unit path, root at (0,0) facing +X (brief S1.10).  Self-avoiding,
# 11 nodes, legal on the 7x7 field.
PATH = [
    (0, 0), (1, 0), (2, 0), (3, 0), (3, 1), (2, 1),
    (1, 1), (0, 1), (0, 2), (1, 2), (2, 2),
]
NODES = [(x * P, y * P) for x, y in PATH]


def _peg(root=False):
    """Downward locating peg, hanging below the board face at z = 0."""
    if root:
        # I1: D4.20 x 2.50, 0.50 x 45 lead -- the snug station peg.
        return fuse([
            cyl(ROOT_PEG_R, -(PEG_LEN - ROOT_PEG_CHAM), 0.0),
            cone(ROOT_PEG_R, ROOT_PEG_R - ROOT_PEG_CHAM, -PEG_LEN, -(PEG_LEN - ROOT_PEG_CHAM)),
        ])
    # I2: D3.00 x 2.50 with a 1.50 long 60 deg conical lead -- slack, self-centring.
    tip_r = PEG_R - PEG_LEAD * math.tan(math.radians(30))
    return fuse([
        cyl(PEG_R, -(PEG_LEN - PEG_LEAD), 0.0),
        cone(PEG_R, tip_r, -PEG_LEN, -(PEG_LEN - PEG_LEAD)),
    ])


def _detent_arm(sign):
    """One compliant film + nose, in the fork frame (0 deg = back to body)."""
    a0, a1 = ARM_ROOT_A, ARM_NOSE_A
    n = 26
    outer, inner = [], []
    for i in range(n):
        t = i / (n - 1)
        a = math.radians(sign * (a0 + (a1 - a0) * t))
        r = ARM_R_ROOT + (ARM_R_TIP - ARM_R_ROOT) * t
        for r_off, dst in ((r + ARM_T / 2, outer), (r - ARM_T / 2, inner)):
            dst.append((r_off * math.cos(a), r_off * math.sin(a)))
    film = poly(outer + list(reversed(inner)), Z_NOTCH_BOT, Z_NOTCH_TOP)
    na = math.radians(sign * ARM_NOSE_A)
    nose = cyl(
        NOSE_R, Z_NOTCH_BOT, Z_NOTCH_TOP,
        NOSE_SEAT_R * math.cos(na), NOSE_SEAT_R * math.sin(na),
    )
    # rigid backing from the spine edge out to the start of the film
    lo, hi = sorted((sign * (SPINE_HALF_NOTCH - 2.0), sign * (ARM_ROOT_A + 1.0)))
    buttress = sector(SPINE_R_IN, BUTTRESS_R_OUT, lo, hi, Z_NOTCH_BOT, Z_NOTCH_TOP)
    return [film, nose, buttress]


def _fork(hinge_no):
    """Everything segment N owns at hinge N, in the fork frame.

    0 deg points back along segment N's body.  Rotated +180 deg and moved to
    the node by the caller.
    """
    # The blind capture bore is cut out of the bottom ear BEFORE the post is
    # fused in.  Cutting it afterwards would eat the bottom 1.21 mm of the post
    # (bore D5.40 > post D5.00) and the pivot would end up a cantilever off the
    # top ear -- exactly the failure the brief's S1.4 capture is there to stop.
    bottom_ear = cut(
        cyl(PUCK_R, Z_BOTEAR_BOT, Z_BOTEAR_TOP),
        [cyl(BORE_R, CAPTURE_BOT, Z_BOTEAR_TOP + 0.01)],
    )
    parts = [
        cyl(PUCK_R, Z_TOPEAR_BOT, Z_TOP),                 # top ear
        bottom_ear,                                       # bottom ear + blind bore
        cyl(POST_R, POST_BOT, Z_TOPEAR_BOT),              # captured pivot post
        # spine: welds the two ears together outside the barrel band
        sector(SPINE_R_IN, BODY_R, -SPINE_HALF_NOTCH, SPINE_HALF_NOTCH,
               Z_BOTEAR_TOP, Z_TOPEAR_BOT),
        # wings: the wider span in the neck sub-band -- these faces are the stop
        sector(SPINE_R_IN, BODY_R, -SPINE_HALF_NECK, SPINE_HALF_NECK,
               Z_BOTEAR_TOP, Z_NECK_TOP),
        _peg(),
    ]
    for sign in (1, -1):
        parts += _detent_arm(sign)
    body = fuse(parts)

    cuts = [
        # 0.40 x 45 chamfer on the post tip: the ring left outside the cone.
        # Kept at r 2.60 < BORE_R 2.70 so it cannot touch the capture bore wall.
        cut(cyl(POST_R + 0.10, POST_BOT - 0.05, POST_BOT + 0.4),
            [cone(POST_R - 0.4, POST_R, POST_BOT, POST_BOT + 0.4)]),
    ]
    # markings: hinge number, and the L / S / R ticks the segment points at
    cuts.append(text_cutter(str(hinge_no), 4.0, ENGRAVE, -6.5, 0.0, Z_TOP, rot=180))
    for letter, ang in (("R", 90.0), ("S", 180.0), ("L", 270.0)):
        a = math.radians(ang)
        cuts.append(
            text_cutter(letter, 3.0, ENGRAVE, 7.0 * math.cos(a), 7.0 * math.sin(a),
                        Z_TOP, rot=ang - 90.0)
        )
        # tick mark pointing at the seat
        tick = box(-0.5, 0.5, 4.6, 5.8, Z_TOP - ENGRAVE, Z_TOP + 0.2)
        cuts.append(rot_z(tick, ang - 90.0))
    return cut(body, cuts)


def _barrel():
    """Everything segment N+1 owns at hinge N, in its own local frame.

    +X is the direction the segment leaves the knuckle, so the neck is at 0 deg
    and the four V-notches sit at +-45 / +-135 from it.
    """
    parts = [
        cyl(BARREL_R, Z_BARREL_BOT, Z_BARREL_TOP),
        # neck, reduced section: passes UNDER the detent arms (play frame)
        box(BARREL_R - 0.6, NECK_R_STEP, -NECK_W / 2, NECK_W / 2, Z_NECK_BOT, Z_NECK_TOP),
        # neck, full band height: this face is the hard stop
        box(NECK_R_STEP, BODY_R, -NECK_W / 2, NECK_W / 2, Z_BARREL_BOT, Z_BARREL_TOP),
    ]
    # flare 5.00 x 5.80 spanning z 3.00..8.80 at r 10, opening to the 12.00 x
    # 12.00 body section spanning z 0..12 at r 13.  The two rectangles are NOT
    # concentric (5.90 vs 6.00), so the small one is offset -0.10 on the YZ
    # plane and the whole loft is then seated on the body centre at z = 6.00.
    flare = (
        cq.Workplane("YZ")
        .workplane(offset=BODY_R)
        .moveTo(0.0, -0.10)
        .rect(NECK_W, Z_BARREL_TOP - Z_BARREL_BOT)
        .workplane(offset=3.0)
        .moveTo(0.0, 0.0)
        .rect(SEG_W, SEG_H)
        .loft()
        .translate((0, 0, SEG_H / 2))
    )
    parts.append(flare)
    body = fuse(parts)

    cuts = [cyl(BORE_R, Z_BARREL_BOT - 0.1, Z_BARREL_TOP + 0.1)]
    r_out = BARREL_R + 0.7  # run the V past the OD so the mouth cuts clean
    half = (r_out - NOTCH_APEX_R) * math.tan(math.radians(NOTCH_HALF_ANGLE))
    # The notch floor drops 0.20 BELOW the detent arm's underside.  Cutting it
    # at Z_NOTCH_BOT -- which is what the brief's "Z extent 3.20 -> 6.20, full
    # notch sub-band" literally says -- makes the floor exactly coplanar with
    # the seated nose's bottom face: 0.00 mm, and every one of the 18 noses
    # prints fused to the barrel it is supposed to click against.
    for ang in (45.0, 135.0, 225.0, 315.0):
        v = poly([(NOTCH_APEX_R, 0.0), (r_out, half), (r_out, -half)],
                 Z_NECK_TOP, Z_NOTCH_TOP + 0.1)
        cuts.append(rot_z(v, ang))
    return cut(body, cuts)


def _segment(k):
    """Segment k (1..10) in its own frame: axis A at the origin, +X to axis B."""
    has_fork = k <= 9      # owns hinge k at B
    has_barrel = k >= 2    # owns hinge k-1 at A

    parts = []
    u0 = 13.0 if has_barrel else 0.0
    mid_end = P - SPINE_R_IN if has_fork else P
    ear_end = P if has_fork else P
    # body: full height where it is clear of a rotating barrel, pulled back to
    # r 6.80 inside the fork's own barrel band.
    if has_fork:
        parts.append(box(u0, ear_end, -SEG_W / 2, SEG_W / 2, Z_BOTEAR_BOT, Z_BOTEAR_TOP))
        parts.append(box(u0, ear_end, -SEG_W / 2, SEG_W / 2, Z_TOPEAR_BOT, Z_TOP))
        parts.append(box(u0, mid_end, -SEG_W / 2, SEG_W / 2, Z_BOTEAR_TOP, Z_TOPEAR_BOT))
    else:
        parts.append(box(u0, P, -SEG_W / 2, SEG_W / 2, 0.0, Z_TOP))

    if has_barrel:
        parts.append(_barrel())
    else:  # segment 1: root end cap + the snug station peg
        parts.append(cyl(CAP_R, 0.0, Z_TOP))
        parts.append(_peg(root=True))

    if has_fork:
        parts.append(rot_z(_fork(k), 180.0).translate((P, 0, 0)))
    else:  # segment 10: tip end cap + peg
        parts.append(cyl(CAP_R, 0.0, Z_TOP, P, 0))
        parts.append(_peg().translate((P, 0, 0)))

    seg = fuse(parts)

    cuts = [text_cutter(str(k), 6.0, ENGRAVE, 21.0, 0.0, Z_TOP)]
    if k == 1:
        # station arrow on the root cap, pointing along segment 1
        cuts.append(poly([(-4.5, 0.0), (-1.0, 2.6), (-1.0, -2.6)],
                         Z_TOP - ENGRAVE, Z_TOP + 0.2))
    return cut(seg, cuts)


def folding_rule_10seg():
    segs = []
    for k in range(1, 11):
        ax, ay = NODES[k - 1]
        bx, by = NODES[k]
        heading = math.degrees(math.atan2(by - ay, bx - ax))
        segs.append(rot_z(_segment(k), heading).translate((ax, ay, 0)))
    # ten rigid links, free to rotate on nine printed pivots: one printed
    # object, deliberately ten shells.  Never fused -- fusing would weld it.
    return cq.Workplane(obj=cq.Compound.makeCompound([s.val() for s in segs]))


# --------------------------------------------------------------------------
# 2. survey_board_7x7
# --------------------------------------------------------------------------
def _node_xy():
    return [(BORDER + c * P, BORDER + r * P) for r in range(7) for c in range(7)]


def _parcel_xy():
    return [
        (BORDER + P / 2 + c * P, BORDER + P / 2 + r * P)
        for r in range(6) for c in range(6)
    ]


def survey_board_7x7():
    top = BOARD_Z
    plate = (
        cq.Workplane("XY")
        .box(BOARD, BOARD, BOARD_PLATE, centered=False)
        .translate((0, 0, BOARD_RIB))
        .edges("|Z")
        .fillet(6.0)
    )
    ribs = [
        cut(box(1.0, BOARD - 1.0, 1.0, BOARD - 1.0, 0.0, BOARD_RIB),
            [box(4.0, BOARD - 4.0, 4.0, BOARD - 4.0, -0.1, BOARD_RIB + 0.1)])
    ]
    for p in [BORDER + i * P for i in range(7)]:
        ribs.append(box(p - 1.25, p + 1.25, 1.0, BOARD - 1.0, 0.0, BOARD_RIB))
        ribs.append(box(1.0, BOARD - 1.0, p - 1.25, p + 1.25, 0.0, BOARD_RIB))
    body = fuse([plate] + ribs)

    cuts = []
    for x, y in _node_xy():  # 49 node sockets, D4.40 x 3.00 with a 0.60 lead-in
        cuts.append(cyl(SOCKET_R, top - SOCKET_DEPTH, top + 0.1, x, y))
        cuts.append(cone(SOCKET_R, SOCKET_R + SOCKET_CHAM,
                         top - SOCKET_CHAM, top + 0.001, x, y))
    for x, y in _parcel_xy():  # 36 parcel dimples
        cuts.append(cyl(DIMPLE_R, top - DIMPLE_DEPTH, top + 0.1, x, y))
        cuts.append(cone(DIMPLE_R, DIMPLE_R + 0.4, top - 0.4, top + 0.001, x, y))
    lo, hi = BORDER, BORDER + 6 * P
    for i in range(7):  # 84 grid edges == 14 node-to-node grooves
        p = BORDER + i * P
        cuts.append(box(lo, hi, p - GRID_W / 2, p + GRID_W / 2, top - ENGRAVE, top + 0.1))
        cuts.append(box(p - GRID_W / 2, p + GRID_W / 2, lo, hi, top - ENGRAVE, top + 0.1))
    for i, ch in enumerate("ABCDEFG"):
        cuts.append(text_cutter(ch, 5.0, ENGRAVE, BORDER + i * P, 4.8, top))
    for i in range(7):
        cuts.append(text_cutter(str(i + 1), 5.0, ENGRAVE, 4.8, BORDER + i * P, top))
    cuts.append(text_cutter("METES AND BOUNDS", 6.0, ENGRAVE, BOARD / 2, BOARD - 4.6, top))
    cuts.append(
        text_cutter("2+ FENCED SIDES = CORNER LOT", 3.5, ENGRAVE,
                    BOARD - 6.0, 4.8, top, halign="right")
    )
    return cut(body, cuts)


# --------------------------------------------------------------------------
# 3 / 5. stakes and pegs
# --------------------------------------------------------------------------
def _silhouette(player, scale, z0, z1):
    """Player head silhouette. `scale` is the outside diameter it fits in."""
    if player == 1:
        s = cyl(scale * 0.5, z0, z1)
    elif player == 2:
        a = scale * 0.87
        s = box(-a / 2, a / 2, -a / 2, a / 2, z0, z1)
        try:
            s = s.edges("|Z").fillet(1.0)
        except Exception:
            pass
    elif player == 3:
        r = scale * 0.5
        pts = [(r * math.cos(math.radians(90 + 120 * i)),
                r * math.sin(math.radians(90 + 120 * i))) for i in range(3)]
        s = poly(pts, z0, z1)
        try:
            s = s.edges("|Z").fillet(1.0)
        except Exception:
            pass
    else:
        a = scale * 0.87
        w = a * 0.35
        s = fuse([box(-a / 2, a / 2, -w / 2, w / 2, z0, z1),
                  box(-w / 2, w / 2, -a / 2, a / 2, z0, z1)])
        try:
            s = s.edges("|Z").fillet(0.8)
        except Exception:
            pass
    return s


def stake(player):
    """Foot D5.60x1.40 / shaft D4.00x9.00 / 45 deg cone to D10 / 3.00 head."""
    z = 0.0
    parts = [cone(2.4, 2.8, 0.0, 0.4), cyl(2.8, 0.4, 1.4)]  # chamfered foot
    parts.append(cyl(2.0, 1.4, 10.4))                        # shaft
    parts.append(cone(2.0, 5.0, 10.4, 13.4))                 # 45 deg support-free
    parts.append(_silhouette(player, 11.5 if player == 3 else 11.49, 13.4, 16.4))
    body = fuse(parts)
    return cut(body, [text_cutter(str(player), 4.0, 0.50, 0, 0, 16.4)])


def score_peg(player):
    parts = [cone(1.5, 2.0, 0.0, 0.5), cyl(2.0, 0.5, 7.0)]
    parts.append(cone(2.0, 4.5, 7.0, 9.5))
    parts.append(_silhouette(player, 9.0 if player == 3 else 8.99, 9.5, 12.5))
    body = fuse(parts)
    return cut(body, [text_cutter(str(player), 3.0, 0.50, 0, 0, 12.5)])


def round_peg():
    across_flats = 11.0
    rc = across_flats / 2 / math.cos(math.radians(30))
    hexa = poly([(rc * math.cos(math.radians(30 + 60 * i)),
                  rc * math.sin(math.radians(30 + 60 * i))) for i in range(6)],
                10.0, 13.0)
    body = fuse([cone(2.0, 2.5, 0.0, 0.5), cyl(2.5, 0.5, 7.0),
                 cone(2.5, 5.5, 7.0, 10.0), hexa])
    return cut(body, [text_cutter("R", 5.0, 0.50, 0, 0, 13.0)])


# --------------------------------------------------------------------------
# 4. score_rail
# --------------------------------------------------------------------------
UPPER_LANE_Y = {1: 61.0, 2: 54.0, 3: 47.0, 4: 40.0}
LOWER_LANE_Y = {1: 28.0, 2: 21.0, 3: 14.0, 4: 7.0}


def score_rail():
    top = RAIL_Z
    body = (
        cq.Workplane("XY")
        .box(RAIL_X, RAIL_Y, RAIL_Z, centered=False)
        .edges("|Z")
        .fillet(4.0)
    )
    cuts = []
    holes = []
    for i in range(21):  # scores 0..20
        for lane_y in UPPER_LANE_Y.values():
            holes.append((10.0 + 10.0 * i, lane_y))
    for i in range(20):  # scores 21..40
        for lane_y in LOWER_LANE_Y.values():
            holes.append((10.0 + 10.0 * i, lane_y))
    for x, y in holes:  # 164 through-holes, chamfered mouth
        cuts.append(cyl(SCORE_HOLE_R, -0.1, top + 0.1, x, y))
        cuts.append(cone(SCORE_HOLE_R, SCORE_HOLE_R + 0.4, top - 0.4, top + 0.001, x, y))
    for i in range(12):  # round track
        cuts.append(cyl(ROUND_HOLE_R, -0.1, top + 0.1, 10.0 + 10.0 * i, 75.0))

    # Engraving bands, top of the rail down.  These are chosen so that no two
    # engraved solids touch: two cut solids that meet exactly tangentially leave
    # a zero-thickness knife edge and the mesh comes out non-manifold.  The
    # brief's own placement put the rounds-per-player note at y = 66.5, straight
    # through the 0-20 score numerals -- glyphs of "13" and of that note met at
    # (139.15, 67.86) and did exactly that.  The note moves onto the round-track
    # line (y = 75, X >= 130) where the brief says it belongs.
    #   y 79.0  "ROUND" heading, right of the track
    #   y 75.0  round holes (X 10..120) + rounds-per-player note (X >= 130)
    #   y 70.3  round numerals 1-12          (68.80 .. 71.80; holes start 72.30)
    #   y 66.5  score numerals 0-20          (64.75 .. 68.25; p1 lane ends 63.20)
    #   y 2.80  score numerals 21-40         ( 1.05 ..  4.55; p4 lane ends  4.80)
    for i in range(21):
        cuts.append(text_cutter(str(i), 3.5, 0.50, 10.0 + 10.0 * i, 66.5, top))
    for i in range(20):
        cuts.append(text_cutter(str(21 + i), 3.5, 0.50, 10.0 + 10.0 * i, 2.8, top))
    for p, y in list(UPPER_LANE_Y.items()) + list(LOWER_LANE_Y.items()):
        cuts.append(_silhouette(p, 5.0, top - 0.50, top + 0.1).translate((4.6, y, 0)))
    for i in range(12):
        cuts.append(text_cutter(str(i + 1), 3.0, 0.50, 10.0 + 10.0 * i, 70.3, top))
    cuts.append(text_cutter("ROUND", 3.5, 0.50, 130.0, 79.0, top, halign="left"))
    cuts.append(text_cutter("2P: 12  3P: 9  4P: 8 ROUNDS", 3.5, 0.50,
                            130.0, 75.0, top, halign="left"))
    return cut(body, cuts)


# --------------------------------------------------------------------------
# build
# --------------------------------------------------------------------------
def parts_table():
    t = [("folding_rule_10seg", lambda: to_print(folding_rule_10seg())),
         ("survey_board_7x7", lambda: to_print(survey_board_7x7()))]
    for p in (1, 2, 3, 4):
        for suffix in "abcdef":
            t.append((f"stake_p{p}_{suffix}", (lambda pp: (lambda: stake(pp)))(p)))
    t.append(("score_rail", score_rail))
    for p in (1, 2, 3, 4):
        t.append((f"score_peg_p{p}", (lambda pp: (lambda: score_peg(pp)))(p)))
    t.append(("round_peg", round_peg))
    return t


# --------------------------------------------------------------------------
# verification -- measured off the exported mesh, not off the CAD kernel.
# OCC's BoundingBox pads curved faces (it reported 14.98 for a 14.50 mm part),
# so every number reported below is read back out of the .stl that will
# actually be sliced.
# --------------------------------------------------------------------------
def read_stl(path):
    data = path.read_bytes()
    n = struct.unpack("<I", data[80:84])[0]
    if len(data) != 84 + 50 * n:
        raise ValueError(f"{path.name}: not a binary STL of {n} facets")
    tris = []
    for i in range(n):
        off = 84 + 50 * i + 12
        v = struct.unpack("<9f", data[off:off + 36])
        tris.append((v[0:3], v[3:6], v[6:9]))
    return tris


def mesh_report(path):
    """bbox, facet count, and manifold check (every edge used exactly twice)."""
    tris = read_stl(path)
    lo = [1e18] * 3
    hi = [-1e18] * 3
    edges = {}
    q = lambda p: (round(p[0], 4), round(p[1], 4), round(p[2], 4))
    for t in tris:
        for p in t:
            for k in range(3):
                lo[k] = min(lo[k], p[k])
                hi[k] = max(hi[k], p[k])
        a, b, c = q(t[0]), q(t[1]), q(t[2])
        for e in ((a, b), (b, c), (c, a)):
            edges[frozenset(e)] = edges.get(frozenset(e), 0) + 1
    bad = sum(1 for v in edges.values() if v != 2)
    return {
        "facets": len(tris),
        "bbox": [round(hi[k] - lo[k], 3) for k in range(3)],
        "nonmanifold_edges": bad,
    }


def _min_gap(a, b):
    from OCP.BRepExtrema import BRepExtrema_DistShapeShape
    e = BRepExtrema_DistShapeShape(a.wrapped, b.wrapped)
    e.Perform()
    return e.Value()


def _placed_segments():
    out = []
    for k in range(1, 11):
        ax, ay = NODES[k - 1]
        bx, by = NODES[k]
        h = math.degrees(math.atan2(by - ay, bx - ax))
        out.append(rot_z(_segment(k), h).translate((ax, ay, 0)).val())
    return out


def rule_interference():
    """The rule is 10 shells that must never touch.  Shared volume between two
    of them is a welded joint; a 0.00 mm gap is the same joint one layer thin.
    Both are checked -- the printable floor is 0.20 mm, the value the brief
    uses for every other clearance in the part."""
    solids = _placed_segments()
    clashes, gaps = [], []
    for i in range(len(solids)):
        for j in range(i + 1, len(solids)):
            bi, bj = solids[i].BoundingBox(), solids[j].BoundingBox()
            if (bi.xmax + 1.0 < bj.xmin or bj.xmax + 1.0 < bi.xmin
                    or bi.ymax + 1.0 < bj.ymin or bj.ymax + 1.0 < bi.ymin):
                continue  # far apart in XY, cannot touch
            v = solids[i].intersect(solids[j]).Volume()
            if abs(v) > 1e-6:
                clashes.append([i + 1, j + 1, round(v, 4)])
            gaps.append([i + 1, j + 1, round(_min_gap(solids[i], solids[j]), 4)])
    return clashes, sorted(gaps, key=lambda g: g[2])


def hinge_sweep():
    """Drive hinge 1 through its whole travel and watch the mechanism work.

    Clash volume is the interference a RIGID model reports, i.e. exactly the
    material the compliant arms have to get out of the way of:
      0 at a detent (joint rests free), >0 between detents (noses riding the
      barrel OD, arms deflected), and >0 again past the hard stop.
    """
    s1 = _segment(1).val()
    s2 = _segment(2).val()
    out = []
    for d in (0.0, 2.0, 2.5, 22.5, 45.0, 67.5, 88.0, 90.0, 92.0, 92.5, 95.0):
        placed = (cq.Workplane(obj=s2).rotate((0, 0, 0), (0, 0, 1), d)
                  .translate((P, 0, 0)).val())
        out.append([d, round(s1.intersect(placed).Volume(), 4)])
    return out


def main():
    rows, results = [], {}
    fine = {"folding_rule_10seg": (0.015, 0.12)}  # the mechanism gets a finer mesh
    for name, fn in parts_table():
        t0 = time.time()
        wp = zero_xy(fn())
        path = OUT / f"{name}.stl"
        tol, ang = fine.get(name, (0.04, 0.2))
        cq.exporters.export(wp, str(path), tolerance=tol, angularTolerance=ang)
        vol = sum(s.Volume() for s in wp.val().Solids())
        n_shell = len(wp.val().Solids())
        m = mesh_report(path)
        kb = path.stat().st_size / 1024
        ok = (kb > 0 and vol > 0 and m["facets"] > 0
              and m["nonmanifold_edges"] == 0
              and max(m["bbox"][0], m["bbox"][1]) <= BED)
        results[name] = dict(m, volume_cm3=round(vol / 1000, 2), shells=n_shell,
                             kb=round(kb, 1), ok=ok)
        rows.append(
            f"{name:22s} {m['bbox'][0]:7.2f} x {m['bbox'][1]:7.2f} x "
            f"{m['bbox'][2]:6.2f}  vol={vol / 1000:7.2f} cm3  shells={n_shell:2d}  "
            f"facets={m['facets']:6d}  nonmanifold={m['nonmanifold_edges']:3d}  "
            f"{kb:8.1f} kB  {time.time() - t0:5.1f}s  {'OK' if ok else 'CHECK'}"
        )
        print(rows[-1], flush=True)

    print("\nrule: 10 shells, pairwise interference and clearance ...", flush=True)
    clash, gaps = rule_interference()
    print("  clashes:", clash if clash else "none -- all 10 shells disjoint")
    print(f"  tightest printed gap anywhere in the rule: {gaps[0][2]:.3f} mm "
          f"(shells {gaps[0][0]}-{gaps[0][1]})")
    print(f"  detent V printed flank gap: {NOTCH_FLANK_GAP:.2f} mm")

    print("\nrule: hinge 1 driven through its travel (rigid-model clash vol) ...",
          flush=True)
    sweep = hinge_sweep()
    for d, v in sweep:
        tag = ("detent seated, free" if v == 0 and (abs(d) < 2.1 or 87 < d < 92.1)
               else "arms deflected, riding the OD" if v > 0 and d < 90
               else "hard stop engaged" if v > 0 else "free")
        print(f"  {d:6.2f} deg  clash {v:8.4f} mm3   {tag}")

    bad = [n for n, r in results.items() if not r["ok"]]
    if clash or gaps[0][2] < 0.19:
        bad.append("folding_rule_10seg:mechanism")
    print(f"\n{len(results)} parts -> {OUT}   failures: {bad or 'none'}")
    (OUT / "_verify.json").write_text(json.dumps({
        "parts": results,
        "rule_shell_clashes": clash,
        "rule_min_gaps_mm": gaps[:6],
        "hinge_sweep_clash_mm3": sweep,
        "detent_flank_gap_mm": round(NOTCH_FLANK_GAP, 3),
    }, indent=1))
    return list(results), clash, bad
    return built


if __name__ == "__main__":
    main()
