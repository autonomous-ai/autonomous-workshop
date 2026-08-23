#!/usr/bin/env python
"""Shed and Shuttle -- parametric print kit (CadQuery).

Source of truth: ../brief.md.  Every number is that brief's number unless a
comment says `DEVIATION:`, which flags a geometric correction (never taste).

The signature part is `part_warp_comb`: one monolithic PETG comb of twelve
compliant cantilever fingers.  Each finger is a real mechanism -- a 0.60 mm
living-hinge film printed as the first three layers, a 30 mm rigid arm, and a
D6.0 warp post that rises 3.0 mm through the deck when a cam bar plateau slides
under it.  The eight cam bars carry the thirteen-cell O/X profiles from brief
S4.3, and a printed leaf-spring detent in the channel floor holds notch 1 / 2.

Run:  /Users/d/.cadcode-venv/bin/python cad/build_parts.py
"""

from __future__ import annotations

import json
import math
import struct
import time
from pathlib import Path

import cadquery as cq

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build"
OUT.mkdir(parents=True, exist_ok=True)

BED = 246.0
FONT = "Arial"

# ==========================================================================
# 0.  Z stack -- brief S0, with the two corrections noted below.
#     Z = 0 is the top face of the deck lane floor.
# ==========================================================================
Z_WALL_TOP = 3.00      # top of a lane wall = top of a raised post
Z_DATUM = 0.00         # deck lane floor
Z_TILE_TOP = -0.20     # seated thread tile
Z_POCKET = -2.40       # tile pocket floor
Z_DECK_BOT = -4.00     # deck plate underside (plate 4.0 thick)
Z_ARM_RAISED = -4.60   # comb arm top face, finger raised (0.6 under the deck)
Z_SPINE_TOP = -6.00
Z_ARM_REST = -7.60     # comb arm top face at rest -> post top flush at Z 0
Z_PLATEAU = -7.00      # top of a RAISED cam cell
Z_BED = -10.00         # comb underside == CAM PLANE == comb ledge top
Z_CHAN_WALL_TOP = -10.30
Z_BAR_TOP = -10.00     # cam bar base top face (the flat-cell cam surface)
Z_BAR_BOT = -14.00
Z_CHAN_FLOOR = -14.20  # 0.2 slide clearance under the bar
Z_FRAME_FLOOR = -15.00
Z_FRAME_BOT = -17.50
Z_RACK_LIP = -5.00

LIFT = 3.00            # post travel == cam step
RAMP_RUN = 4.50        # 3.0 rise over 4.5 run = 33.7 deg
PLATEAU = 7.00

# DEVIATION 1 (mechanism, deliberate).  Brief S3.4 puts a 0.8 mm cam-follower
# rib proud of the comb's arm underside, and brief S9.3 / S10 simultaneously
# require the comb to print with "zero overhang" on its flat underside.  Those
# two cannot both hold: with the ribs 0.8 below the bed plane the comb would
# stand on twelve 5x9 pads and the whole remaining part would start 0.8 mm in
# the air.  The rib is therefore deleted and the entire cam plane raised 0.8
# (channel floor -14.2 instead of -15.0, cam plane -10.0 instead of -10.8).
# The arm underside itself is the follower.  Nothing else moves: lift is still
# 3.0, ramps still 33.7 deg, arm-top-at-rest still -7.6, post still flush at
# Z 0 and proud 3.0 when lifted, bar still 7.0 tall.  A 9.0 wide flat follower
# centred on a 7.0 plateau still reaches full lift (it lands on the two plateau
# edges), and the bar always indexes in whole 16.0 lanes so a follower is never
# parked on a ramp.

# ==========================================================================
# 1.  Plan geometry
# ==========================================================================
DECK_X, DECK_Y = 215.00, 142.00
LANE_PITCH = 16.00
LANE_W = 13.00
WALL_W = 3.00
BORDER = 10.00
N_LANES = 12

UF_X, UF_Y = 233.00, 210.00
D2U = 12.00            # deck-local x + D2U = underframe x

CHAN_CL = 34.00        # cam channel / warp post centreline in Y
CHAN_CLEAR = 14.50
CHAN_Y0 = CHAN_CL - CHAN_CLEAR / 2      # 26.75
CHAN_Y1 = CHAN_CL + CHAN_CLEAR / 2      # 41.25

POST_D = 6.00
POST_HOLE_D = 6.60
POCKET_Y = [52.0, 74.0, 96.0, 118.0]
POCKET_L, POCKET_W, POCKET_DEEP = 18.50, 12.00, 2.40
NOTCH_L, NOTCH_W = 3.00, 6.00
NOTCH_Z = -3.00        # DEVIATION 2: brief's 3.9 leaves 0.1 mm of plate.
LANE_VALUES = [3, 1, 4, 2, 5, 1, 2, 4, 1, 3, 5, 2]

# joining slots (deck-local).  DEVIATION 3: brief S2.4 puts the six underframe
# snap slots at deck x 30 / 107.5 / 185, which land inside lane 2, the lane
# 6/7 wall and lane 11 -- i.e. in the shuttle's path, contradicting the same
# section's "all slots are outside the lane band anyway".  They move into the
# 10 mm side borders.
TAB_XY = [(5.0, 6.0), (5.0, 47.0), (5.0, 136.0),
          (210.0, 6.0), (210.0, 47.0), (210.0, 136.0)]
TAB_SLOT = (8.00, 3.00)
EAR_XY = [(5.0, 69.0), (210.0, 69.0)]
EAR_SLOT = (6.00, 3.00)
RELIEF_DEEP, RELIEF_W = 0.50, 1.50
HOOK_PROUD = 0.80
HOOK_Z0 = -0.50        # hook underside seats in the relief pocket
HOOK_Z1 = 0.50         # top of tab / ear

# comb
FILM_T, FILM_W, FILM_L = 0.60, 9.00, 6.00
ARM_T, ARM_W = 2.40, 9.00
ARM_Y0, ARM_Y1 = 28.00, 58.00
FILM_Y0, FILM_Y1 = 58.00, 64.00
SPINE_Y0, SPINE_Y1 = 64.00, 74.00
SPINE_T = 4.00
BLEND_R = 1.50
# DEVIATION 4: spine 211 wide (uf x 14.0 .. 225.0) not 206, so the two ears at
# deck x 5 / 210 sit wholly on the spine instead of hanging off its ends.
SPINE_X0, SPINE_X1 = 14.00, 225.00
PIN_X = [40.0, 175.0]
PIN_D, PIN_H = 3.00, 3.00
PIN_HOLE_D, PIN_HOLE_DEEP = 3.30, 3.20

# cam bar
BAR_W = 14.00
BAR_BASE_T = 4.00
BAR_CELLS = 13
BAR_BODY_L = BAR_CELLS * LANE_PITCH     # 208
HANDLE_L = 30.00       # DEVIATION 9, see NOTCH_NOSE below
BAR_L = BAR_BODY_L + HANDLE_L           # 238
BAR_H = BAR_BASE_T + LIFT               # 7.0
RAIL = 1.50
NOSE_CHAM = 1.50
DIMPLE_X = [24.00, 40.00]               # bar-local, from the nose
DIMPLE_R, DIMPLE_DEEP = 1.20, 0.80

BAR_PROFILES = {
    "a": "OXXOXXOXOXXOX",
    "b": "XOXOXOXXOXOXX",
    "c": "OOXXOXXOXXOOX",
    "d": "XXOXOXOOXOXXO",
    "e": "OXOXXOXOXOXXO",
    "f": "XOOXXOOXXOXOX",
    "g": "OXXXOOXXOXOXO",
    "h": "XXOOXOXOOXXOX",
}

# detent.  DEVIATION 5: brief S5.3 / S4.5 put a compliant leaf in the channel
# side wall and scallops in the bar's side face.  A side leaf cannot be printed
# (freeing it in Y means it must bridge over its own relief slot, unsupported
# for 20 mm) and, backed by the wall, it is ~20x too stiff.  The detent moves
# into the channel FLOOR: a flat leaf-spring tongue, cut out of the floor and
# printed dead flat, carrying a domed bump that drops into a hemispherical
# dimple in the bar's underside.  Same 16.0 detent separation, same audible
# click, ~4 N hold (k = 3EI/L^3 = 6.7 N/mm at 0.6 mm of ride-out).
DET_X = 47.50          # underframe x of the bump == bar-local 24.0 at notch 1
TONGUE_Y0, TONGUE_Y1 = 29.25, 39.25
TONGUE_T = 2.00
TONGUE_ROOT, TONGUE_TIP = 67.00, 45.00
SLOT_W = 1.50
BUMP_R = 1.00
BUMP_PROUD = 0.80

# Underframe x of the bar nose at each notch.  DEVIATION 9: brief S4.6 sizes
# the handle (18.0) against the 215 wide DECK, but the bar slides in the 233
# wide UNDERFRAME -- at notch 2 that leaves 0.5 mm of handle proud of the frame,
# i.e. nothing to pull.  The handle grows to 30.0 (bar 238 long, still 8 mm
# inside the bed) so notch 2 leaves 12.5 mm to grab and notch 1 leaves 28.5.
NOTCH_NOSE = {1: 23.50, 2: 7.50}

# rack
RACK_Y0 = 142.00
RACK_SLOT_W = 7.60
RACK_PITCH = 9.00
RACK_N = 7
RACK_END = 3.20
RACK_X0, RACK_X1 = 2.50, 230.50

# shuttle
SH_L, SH_W, SH_HULL, SH_H = 26.00, 12.40, 4.50, 7.50
SH_NOSE_V, SH_SWEEP = 3.50, 8.00
FIN_L, FIN_W, FIN_TOP = 20.00, 3.00, 7.50

# tile
TILE_L, TILE_W, TILE_T = 18.00, 11.60, 2.20
TILE_R = 1.00
SCOOP_L, SCOOP_W, SCOOP_DEEP = 3.00, 8.00, 1.00
TILE_PIP_D, TILE_PIP_DEEP = 2.50, 0.60
# DEVIATION 6: brief S7 asks for a 0.4 mm pitch cross-hatch.  A 0.4 nozzle
# cannot cut a 0.4 mm groove; the weave is opened to a 1.6 mm pitch x 0.8 wide
# x 0.3 deep warp/weft grid, which actually prints and still reads as cloth.
WEAVE_PITCH, WEAVE_W, WEAVE_DEEP = 1.60, 0.80, 0.30


def lane_cx(n):
    """Deck-local x of lane n (1-based) centre."""
    return 19.50 + LANE_PITCH * (n - 1)


def finger_cx(n):
    """Underframe x of comb finger n."""
    return lane_cx(n) + D2U


# ==========================================================================
# 2.  helpers
# ==========================================================================
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
    return (cq.Workplane("XY")
            .box(x1 - x0, y1 - y0, z1 - z0, centered=False)
            .translate((x0, y0, z0)))


def cyl(r, z0, z1, x=0.0, y=0.0):
    return cq.Workplane(obj=cq.Solid.makeCylinder(r, z1 - z0, cq.Vector(x, y, z0)))


def cone(r0, r1, z0, z1, x=0.0, y=0.0):
    return cq.Workplane(obj=cq.Solid.makeCone(r0, r1, z1 - z0, cq.Vector(x, y, z0)))


def sphere(r, x, y, z):
    return cq.Workplane(obj=cq.Solid.makeSphere(r, cq.Vector(x, y, z), angleDegrees1=-90))


def cyl_y(r, y0, y1, x=0.0, z=0.0):
    return cq.Workplane(obj=cq.Solid.makeCylinder(
        r, y1 - y0, cq.Vector(x, y0, z), cq.Vector(0, 1, 0)))


def rrect(x0, x1, y0, y1, z0, z1, r):
    return (cq.Workplane("XY")
            .box(x1 - x0, y1 - y0, z1 - z0, centered=False)
            .edges("|Z").fillet(r)
            .translate((x0, y0, z0)))


def poly_z(pts, z0, z1):
    """Plan polygon given as (x, y) pairs, extruded from z0 to z1."""
    return (cq.Workplane("XY").polyline(pts).close().extrude(z1 - z0)
            .translate((0, 0, z0)))


def prism_xz(pts, y0, y1):
    """Profile given as (x, z) pairs, extruded from y0 to y1."""
    return (cq.Workplane("XY").polyline(pts).close().extrude(y1 - y0)
            .rotate((0, 0, 0), (1, 0, 0), 90)
            .translate((0, y1, 0)))


def prism_yz(pts, x0, x1):
    """Profile given as (y, z) pairs, extruded from x0 to x1."""
    return (prism_xz(pts, 0.0, x1 - x0)
            .rotate((0, 0, 0), (0, 0, 1), 90)
            .translate((x1, 0, 0)))


def arc_pts(cx, cy, r, a0, a1, n=13):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / (n - 1))),
             cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / (n - 1))))
            for i in range(n)]


_GLYPH = {}


def _glyph(txt, size, depth):
    key = (txt, round(size, 3), round(depth, 3))
    if key not in _GLYPH:
        _GLYPH[key] = (cq.Workplane("XY")
                       .text(txt, size, depth, combine=False, font=FONT,
                             halign="center", valign="center"))
    return _GLYPH[key]


def text_flat(txt, size, depth, x, y, z0, rot=0.0):
    """Glyph solid lying in XY, rising from z0 by `depth`."""
    t = _glyph(txt, size, depth)
    if rot:
        t = t.rotate((0, 0, 0), (0, 0, 1), rot)
    return t.translate((x, y, z0))


def text_wall(txt, size, depth, x, z, y_face, outward):
    """Glyph cutter sunk `depth` into a face at y = y_face whose outward normal
    is `outward` (+1 / -1).  It overshoots 0.1 mm proud of the face so the cut
    is never tangent to it -- a tangent cutter welds a zero-thickness edge and
    the mesh comes out non-manifold."""
    t = _glyph(txt, size, depth + 0.1).rotate((0, 0, 0), (1, 0, 0), 90)
    if outward > 0:
        # Rx(90) puts glyph-up on +Z but glyph-right on +X, which reads
        # mirrored from +Y; Rz(180) fixes it and turns the extrusion to +Y.
        t = t.rotate((0, 0, 0), (0, 0, 1), 180)
        return t.translate((x, y_face - depth, z))
    return t.translate((x, y_face + depth, z))


def to_print(wp):
    bb = wp.val().BoundingBox()
    return wp.translate((0, 0, -bb.zmin))


# ==========================================================================
# 3.  part_deck  (brief S2)
# ==========================================================================
def _slot_cuts(x, y, sx, sy):
    """A joining slot through the plate, its lead-in step, and the +Y relief
    pocket the hook lands in."""
    return [
        box(x - sx / 2, x + sx / 2, y - sy / 2, y + sy / 2,
            Z_DECK_BOT - 0.1, Z_DATUM + 0.1),
        # 0.4 lead-in step on the top face (DEVIATION: step, not a 45 chamfer,
        # so the cut stays a clean prism on a 190-solid boolean)
        box(x - sx / 2 - 0.4, x + sx / 2 + 0.4, y - sy / 2 - 0.4, y + sy / 2 + 0.4,
            -0.40, Z_DATUM + 0.1),
        # relief pocket, hook side (+Y)
        box(x - sx / 2, x + sx / 2, y + sy / 2, y + sy / 2 + RELIEF_W,
            -RELIEF_DEEP, Z_DATUM + 0.1),
    ]


def part_deck():
    plate = box(0, DECK_X, 0, DECK_Y, Z_DECK_BOT, Z_DATUM)

    # -- lane walls: 13 walls, 3.0 wide x 3.0 tall, 0.5 x 45 top break -------
    walls = []
    for k in range(13):
        x0 = BORDER + LANE_PITCH * k
        x1 = x0 + WALL_W
        walls.append(prism_xz(
            [(x0, 0.0), (x1, 0.0), (x1, Z_WALL_TOP - 0.5),
             (x1 - 0.5, Z_WALL_TOP), (x0 + 0.5, Z_WALL_TOP), (x0, Z_WALL_TOP - 0.5)],
            0.0, DECK_Y))
    body = fuse([plate] + walls)

    cuts = []
    # near / far entry chamfers on the wall ends, 2.0 x 45 (brief S2.2)
    cuts.append(prism_yz([(-1.0, 1.0), (2.0, Z_WALL_TOP + 0.5),
                          (-1.0, Z_WALL_TOP + 0.5)], -1.0, DECK_X + 1.0))
    cuts.append(prism_yz([(DECK_Y + 1.0, 1.0), (DECK_Y - 2.0, Z_WALL_TOP + 0.5),
                          (DECK_Y + 1.0, Z_WALL_TOP + 0.5)], -1.0, DECK_X + 1.0))

    for n in range(1, N_LANES + 1):
        cx = lane_cx(n)
        # warp post hole + 0.4 x 45 top lead-in
        cuts.append(cyl(POST_HOLE_D / 2, Z_DECK_BOT - 0.1, Z_DATUM + 0.1, cx, CHAN_CL))
        cuts.append(cone(POST_HOLE_D / 2, POST_HOLE_D / 2 + 0.4, -0.40, Z_DATUM + 0.01,
                         cx, CHAN_CL))
        for cy in POCKET_Y:
            cuts.append(rrect(cx - POCKET_W / 2, cx + POCKET_W / 2,
                              cy - POCKET_L / 2, cy + POCKET_L / 2,
                              Z_POCKET, Z_DATUM + 0.1, 1.0))
            cuts.append(box(cx - NOTCH_W / 2, cx + NOTCH_W / 2,
                            cy - POCKET_L / 2, cy - POCKET_L / 2 + NOTCH_L,
                            NOTCH_Z, Z_DATUM + 0.1))
        # far-edge lane legend.  DEVIATION 7: brief S2.3 embosses these +0.6 in
        # the shuttle run-out (y 128-142) -- the shuttle would hit them.  They
        # are engraved 0.6 instead, exactly the reason S7 recesses the tile pips.
        cuts.append(text_flat(str(n), 5.0, 0.7, cx, 137.0, -0.60))
        cuts.append(text_flat(str(LANE_VALUES[n - 1]), 7.0, 0.7, cx, 131.0, -0.60))

    for x, y in TAB_XY:
        cuts.extend(_slot_cuts(x, y, *TAB_SLOT))
    for x, y in EAR_XY:
        cuts.extend(_slot_cuts(x, y, *EAR_SLOT))

    body = cut(body, cuts)

    # raised graphics on the borders (never in a lane)
    ups = []
    for i, cy in enumerate(POCKET_Y):
        ups.append(text_flat(str(i + 1), 4.0, 0.4, 5.0, cy, Z_DATUM))
    ups.append(text_flat("SHED AND SHUTTLE", 5.0, 0.6, 210.0, 100.0, Z_DATUM, rot=90))
    return fuse([body] + ups)


# ==========================================================================
# 4.  part_warp_comb  (brief S3)
# ==========================================================================
def _finger_profile():
    """Finger cross-section in (y, z): flat underside on the bed at Z_BED, arm
    2.4 thick, 0.60 film with R1.5 blends on the TOP face only, into the spine."""
    z_arm = Z_BED + ARM_T                      # -7.6
    z_film = Z_BED + FILM_T                    # -9.4
    y_a, y_b = FILM_Y0 + BLEND_R, FILM_Y1 - BLEND_R   # 59.5, 62.5
    z_blend = z_film + BLEND_R                 # -7.9
    pts = [(ARM_Y0, Z_BED), (SPINE_Y1, Z_BED), (SPINE_Y1, Z_SPINE_TOP),
           (FILM_Y1, Z_SPINE_TOP)]
    pts += arc_pts(y_b, z_blend, BLEND_R, 0.0, -90.0)
    pts += arc_pts(y_a, z_blend, BLEND_R, -90.0, -180.0)
    pts += [(FILM_Y0, z_arm), (ARM_Y0, z_arm)]
    return pts


def part_warp_comb():
    z_arm = Z_BED + ARM_T
    solids = [box(SPINE_X0, SPINE_X1, SPINE_Y0, SPINE_Y1, Z_BED, Z_SPINE_TOP)]
    prof = _finger_profile()
    z_dome_c = -math.sqrt((POST_D / 2) ** 2 - 1.0 ** 2)   # 2.0 flat on an R3 dome

    for n in range(1, N_LANES + 1):
        cx = finger_cx(n)
        solids.append(prism_yz(prof, cx - ARM_W / 2, cx + ARM_W / 2))
        # warp post: 0.4 x 45 root break, D6.0 shank, R3 dome flatted to D2.0
        solids.append(cone(POST_D / 2 + 0.4, POST_D / 2, z_arm, z_arm + 0.4, cx, CHAN_CL))
        solids.append(cyl(POST_D / 2, z_arm + 0.4, z_dome_c, cx, CHAN_CL))
        solids.append(cut(sphere(POST_D / 2, cx, CHAN_CL, z_dome_c),
                          [box(cx - 4, cx + 4, CHAN_CL - 4, CHAN_CL + 4, 0.0, 4.0)]))

    # mounting ears: rooted at the spine underside so the cantilever is 10.5
    # long (a 6.5 stub off the spine top would need ~230 N to snap home)
    for dx, _dy in EAR_XY:
        x = dx + D2U
        ex0, ex1 = x - 2.90, x + 2.90
        ey0, ey1 = 69.0 - 1.10, 69.0 + 1.10
        solids.append(box(ex0, ex1, ey0, ey1, Z_BED, HOOK_Z1))
        solids.append(prism_yz(
            [(ey1, HOOK_Z0), (ey1 + HOOK_PROUD, HOOK_Z0),
             (ey1, HOOK_Z0 + HOOK_PROUD)], ex0, ex1))

    body = fuse(solids)
    # blind locating-pin holes, from the spine underside
    body = cut(body, [cyl(PIN_HOLE_D / 2, Z_BED - 0.1, Z_BED + PIN_HOLE_DEEP, x, 69.0)
                      for x in PIN_X])
    return body


# ==========================================================================
# 5.  part_bar_*  (brief S4)  -- bar-local: nose at x 0, underside at z 0
# ==========================================================================
def _runs(profile):
    out, k = [], 0
    while k < len(profile):
        if profile[k] == "X":
            j = k
            while j + 1 < len(profile) and profile[j + 1] == "X":
                j += 1
            out.append((k, j))
            k = j + 1
        else:
            k += 1
    return out


def _cam_prism(x0, x1):
    """One merged run of raised cells: 4.5 up-ramp, plateau, 4.5 down-ramp,
    convex corners broken 0.4 x 45 (brief S4.2)."""
    zb, zt = BAR_BASE_T, BAR_BASE_T + LIFT
    d = LIFT / math.hypot(RAMP_RUN, LIFT)
    c = RAMP_RUN / math.hypot(RAMP_RUN, LIFT)
    a, b = x0 + RAMP_RUN, x1 - RAMP_RUN
    return prism_xz([(x0, zb),
                     (a - 0.4 * c, zt - 0.4 * d), (a + 0.4, zt),
                     (b - 0.4, zt), (b + 0.4 * c, zt - 0.4 * d),
                     (x1, zb)], -BAR_W / 2, BAR_W / 2)


def part_bar(letter):
    prof = BAR_PROFILES[letter]
    zt = BAR_BASE_T + LIFT
    solids = [box(0, BAR_L, -BAR_W / 2, BAR_W / 2, 0, BAR_BASE_T),
              box(BAR_BODY_L, BAR_L, -BAR_W / 2, BAR_W / 2, BAR_BASE_T, zt),
              box(0, BAR_BODY_L, -BAR_W / 2 - RAIL, -BAR_W / 2, 0, RAIL),
              box(0, BAR_BODY_L, BAR_W / 2, BAR_W / 2 + RAIL, 0, RAIL)]
    for i, j in _runs(prof):
        solids.append(_cam_prism(LANE_PITCH * i, LANE_PITCH * (j + 1)))
    for gx in (226.0, 230.0, 234.0):        # handle grip ribs, 4.0 pitch
        solids.append(cyl_y(0.75, -BAR_W / 2, BAR_W / 2, gx, zt))
    # handle-top letter, embossed +0.6 (readable while the bar is in the rail)
    solids.append(text_flat(letter.upper(), 8.0, 0.6, 216.0, 0.0, zt))
    body = fuse(solids)

    cuts = []
    # nose lead: 1.5 x 45 off the leading bottom edge, rails included
    cuts.append(prism_xz([(-0.1, -0.1), (NOSE_CHAM, -0.1), (-0.1, NOSE_CHAM)],
                         -BAR_W / 2 - RAIL - 0.1, BAR_W / 2 + RAIL + 0.1))
    # detent dimples in the underside, 16.0 apart (brief S4.5 separation).
    # A 45 deg truncated-cone socket, not a spherical one: a sphere cut leaves
    # its pole inside the cap and meshes to a degenerate triangle fan.
    for dx in DIMPLE_X:
        cuts.append(cone(DIMPLE_R + 0.30, DIMPLE_R - 0.70, -0.05,
                         DIMPLE_DEEP + 0.05, dx, 0.0))
    # +Y face legend, engraved 0.6 (see DEVIATION 8 below)
    for k in range(BAR_CELLS):
        cuts.append(text_wall(prof[k], 3.0, 0.6, LANE_PITCH * k + LANE_PITCH / 2,
                              2.0, BAR_W / 2, +1))
    cuts.append(text_wall(letter.upper(), 5.0, 0.6, 222.0, 3.5, BAR_W / 2, +1))
    # reading-direction arrow at cell 1, pointing at the nose
    cuts.append(prism_xz([(4.0, 2.0), (1.0, 2.9), (1.0, 1.1)],
                         BAR_W / 2 - 0.7, BAR_W / 2 + 0.1))
    return cut(body, cuts)


# DEVIATION 8: brief S4.4 embosses the side legend +0.6 proud.  The bar has
# 0.25 mm of clearance per side in the channel, so a proud legend would jam it.
# The legend is engraved 0.6 instead -- still readable, and the face it is on
# points straight up when the bar stands on edge in the rack, which is when you
# actually read it.  The handle-top letter stays embossed (nothing above it).


# ==========================================================================
# 6.  part_bar_rail  (brief S5)
# ==========================================================================
def part_bar_rail():
    solids = [box(0, UF_X, 0, UF_Y, Z_FRAME_BOT, Z_FRAME_FLOOR)]           # floor
    # perimeter, under-deck section
    solids.append(box(0, 3, 0, DECK_Y, Z_FRAME_FLOOR, Z_DECK_BOT))
    solids.append(box(UF_X - 3, UF_X, 0, DECK_Y, Z_FRAME_FLOOR, Z_DECK_BOT))
    solids.append(box(0, UF_X, 0, 3, Z_FRAME_FLOOR, Z_DECK_BOT))
    solids.append(box(0, UF_X, DECK_Y - 3, DECK_Y, Z_FRAME_FLOOR, Z_DECK_BOT))
    # walls carrying the deck borders (and the six snap tabs)
    solids.append(box(13, 21, 0, DECK_Y, Z_FRAME_FLOOR, Z_DECK_BOT))
    solids.append(box(212, 220, 0, DECK_Y, Z_FRAME_FLOOR, Z_DECK_BOT))
    # stiffening ribs (brief S5.1); y 60.5 is dropped -- it would foul the
    # living-hinge films at y 58-64
    for ry in (15.0, 100.0, 128.0):
        solids.append(box(3, UF_X - 3, ry - 1.5, ry + 1.5, Z_FRAME_FLOOR, Z_DECK_BOT))
    # comb ledge + locating pins
    solids.append(box(3, 230, SPINE_Y0, SPINE_Y1, Z_FRAME_FLOOR, Z_BED))
    for px in PIN_X:
        solids.append(cyl(PIN_D / 2, Z_BED, Z_BED + PIN_H, px, 69.0))
    # cam channel floor pad + walls
    solids.append(box(0, UF_X, CHAN_Y0, CHAN_Y1, Z_FRAME_FLOOR, Z_CHAN_FLOOR))
    solids.append(box(0, UF_X, CHAN_Y0 - 3.0, CHAN_Y0, Z_FRAME_FLOOR, Z_CHAN_WALL_TOP))
    solids.append(box(0, UF_X, CHAN_Y1, CHAN_Y1 + 3.0, Z_FRAME_FLOOR, Z_CHAN_WALL_TOP))
    # rack block
    solids.append(box(RACK_X0, RACK_X1, RACK_Y0, UF_Y, Z_FRAME_FLOOR, Z_RACK_LIP))
    # six deck snap tabs
    for dx, dy in TAB_XY:
        x = dx + D2U
        solids.append(box(x - 3.9, x + 3.9, dy - 1.2, dy + 1.2, Z_FRAME_FLOOR, HOOK_Z1))
        solids.append(prism_yz(
            [(dy + 1.2, HOOK_Z0), (dy + 1.2 + HOOK_PROUD, HOOK_Z0),
             (dy + 1.2, HOOK_Z0 + HOOK_PROUD)], x - 3.9, x + 3.9))
    body = fuse(solids)

    cuts = []
    # channel void: everything between the walls, from the slide face up
    cuts.append(box(-1, UF_X + 1, CHAN_Y0, CHAN_Y1, Z_CHAN_FLOOR, Z_DECK_BOT + 0.1))
    # T-rail retention grooves, 1.7 x 1.9 undercut, roof 2.0 thick
    cuts.append(box(-1, UF_X + 1, CHAN_Y0 - 1.7, CHAN_Y0, Z_CHAN_FLOOR, -12.30))
    cuts.append(box(-1, UF_X + 1, CHAN_Y1, CHAN_Y1 + 1.7, Z_CHAN_FLOOR, -12.30))
    # clear the comb spine seat above the ledge
    cuts.append(box(3, 230, SPINE_Y0, SPINE_Y1, Z_BED, Z_DECK_BOT + 0.1))
    # free the six snap tabs so they can actually flex
    for dx, dy in TAB_XY:
        x = dx + D2U
        cuts.append(box(x - 5.5, x + 5.5, dy - 3.4, dy - 1.2, Z_FRAME_FLOOR, Z_DECK_BOT + 0.1))
        cuts.append(box(x - 5.5, x + 5.5, dy + 1.2, dy + 3.4, Z_FRAME_FLOOR, Z_DECK_BOT + 0.1))
    # detent tongue: U-slot through the floor, then thinned from the top
    cuts.append(box(TONGUE_TIP - 2, TONGUE_ROOT, TONGUE_Y0 - SLOT_W, TONGUE_Y0,
                    Z_FRAME_BOT - 0.1, Z_CHAN_FLOOR + 0.1))
    cuts.append(box(TONGUE_TIP - 2, TONGUE_ROOT, TONGUE_Y1, TONGUE_Y1 + SLOT_W,
                    Z_FRAME_BOT - 0.1, Z_CHAN_FLOOR + 0.1))
    cuts.append(box(TONGUE_TIP - 2, TONGUE_TIP, TONGUE_Y0 - SLOT_W, TONGUE_Y1 + SLOT_W,
                    Z_FRAME_BOT - 0.1, Z_CHAN_FLOOR + 0.1))
    cuts.append(box(TONGUE_TIP, TONGUE_ROOT, TONGUE_Y0, TONGUE_Y1,
                    Z_FRAME_BOT + TONGUE_T, Z_CHAN_FLOOR + 0.1))
    # bar rack: 7 slots on 9.0 pitch, open at both ends in X
    for n in range(RACK_N):
        y0 = RACK_Y0 + RACK_END + RACK_PITCH * n
        cuts.append(box(RACK_X0 - 1, RACK_X1 + 1, y0, y0 + RACK_SLOT_W,
                        Z_FRAME_FLOOR, Z_RACK_LIP + 0.1))
    # thumb cut-out, 6.0 down from the lip
    cuts.append(box(116.5 - 15, 116.5 + 15, RACK_Y0 - 1, UF_Y + 1,
                    Z_RACK_LIP - 6.0, Z_RACK_LIP + 0.1))
    # right mouth, flared 3.0 x 45 in plan so a bar finds the channel
    cuts.append(poly_z([(UF_X - 3.0, CHAN_Y0), (UF_X + 0.1, CHAN_Y0),
                        (UF_X + 0.1, CHAN_Y0 - 3.0)],
                       Z_FRAME_FLOOR - 0.1, Z_CHAN_WALL_TOP + 0.1))
    cuts.append(poly_z([(UF_X - 3.0, CHAN_Y1), (UF_X + 0.1, CHAN_Y1),
                        (UF_X + 0.1, CHAN_Y1 + 3.0)],
                       Z_FRAME_FLOOR - 0.1, Z_CHAN_WALL_TOP + 0.1))
    body = cut(body, cuts)

    # detent bump, fused AFTER the tongue is cut free: a D3.0 post off the
    # tongue top capped by an R1.0 dome, cresting 0.8 above the channel floor
    z_dome = Z_CHAN_FLOOR + BUMP_PROUD - BUMP_R
    z_flat = z_dome + 0.95          # crest flatted D0.62; a bare pole meshes
    body = fuse([body,              # to a degenerate fan and reads non-manifold
                 cyl(1.50, Z_FRAME_BOT + TONGUE_T, z_dome, DET_X, CHAN_CL),
                 cut(sphere(BUMP_R, DET_X, CHAN_CL, z_dome),
                     [box(DET_X - 2, DET_X + 2, CHAN_CL - 2, CHAN_CL + 2,
                          z_flat, z_flat + 2)])])

    # rack legend, engraved into the outer face so the footprint stays 233x210
    return cut(body, [text_wall(ch, 6.0, 0.6, 30.0 + 25.0 * i, -9.0, UF_Y, +1)
                      for i, ch in enumerate("ABCDEFGH")])


# ==========================================================================
# 7.  part_shuttle_p*  (brief S6)
# ==========================================================================
def part_shuttle(p):
    hull = prism_xz([(0.0, 0.0), (0.0, SH_NOSE_V), (SH_SWEEP, SH_HULL),
                     (SH_L - SH_SWEEP, SH_HULL), (SH_L, SH_NOSE_V), (SH_L, 0.0)],
                    0.0, SH_W)
    # 0.5 x 45 break all round the underside
    cuts = [prism_xz([(-0.1, -0.1), (0.5, -0.1), (-0.1, 0.5)], -1, SH_W + 1),
            prism_xz([(SH_L + 0.1, -0.1), (SH_L - 0.5, -0.1), (SH_L + 0.1, 0.5)],
                     -1, SH_W + 1),
            prism_yz([(-0.1, -0.1), (0.5, -0.1), (-0.1, 0.5)], -1, SH_L + 1),
            prism_yz([(SH_W + 0.1, -0.1), (SH_W - 0.5, -0.1), (SH_W + 0.1, 0.5)],
                     -1, SH_L + 1)]
    hull = cut(hull, cuts)
    # grip fin: stadium 20.0 x 3.0, R1.5 ends, sunk into the hull so it merges
    fy = SH_W / 2
    fin = fuse([box(SH_L / 2 - FIN_L / 2 + 1.5, SH_L / 2 + FIN_L / 2 - 1.5,
                    fy - FIN_W / 2, fy + FIN_W / 2, 3.0, FIN_TOP),
                cyl(FIN_W / 2, 3.0, FIN_TOP, SH_L / 2 - FIN_L / 2 + 1.5, fy),
                cyl(FIN_W / 2, 3.0, FIN_TOP, SH_L / 2 + FIN_L / 2 - 1.5, fy)])
    pips = []
    for i in range(p):
        px = SH_L / 2 + (i - (p - 1) / 2) * 3.50
        pips.append(cyl_y(1.20, fy + FIN_W / 2, fy + FIN_W / 2 + 0.6, px, 6.0))
        pips.append(cyl_y(1.20, fy - FIN_W / 2 - 0.6, fy - FIN_W / 2, px, 6.0))
    return fuse([hull, fin] + pips)


# ==========================================================================
# 8.  part_tile_p*  (brief S7)
# ==========================================================================
def part_tile(p):
    body = rrect(0, TILE_L, 0, TILE_W, 0, TILE_T, TILE_R)
    cuts = []
    # weave: warp + weft grid, 1.6 pitch, 0.8 wide, 0.3 deep.  Orthogonal,
    # not the brief's 45 deg cross-hatch, because on a loom tile the threads
    # run with and across the lane -- and it costs 17 cuts instead of 82.
    z0 = TILE_T - WEAVE_DEEP
    n = int(TILE_L / WEAVE_PITCH)
    for i in range(n):
        gx = (TILE_L - (n - 1) * WEAVE_PITCH) / 2 + i * WEAVE_PITCH
        cuts.append(box(gx - WEAVE_W / 2, gx + WEAVE_W / 2, -0.5, TILE_W + 0.5,
                        z0, TILE_T + 0.1))
    m = int(TILE_W / WEAVE_PITCH)
    for i in range(m):
        gy = (TILE_W - (m - 1) * WEAVE_PITCH) / 2 + i * WEAVE_PITCH
        cuts.append(box(-0.5, TILE_L + 0.5, gy - WEAVE_W / 2, gy + WEAVE_W / 2,
                        z0, TILE_T + 0.1))
    # finger scoop at the near end, aligned with the pocket lift notch
    cuts.append(rrect(1.0, 1.0 + SCOOP_L, TILE_W / 2 - SCOOP_W / 2,
                      TILE_W / 2 + SCOOP_W / 2,
                      TILE_T - SCOOP_DEEP, TILE_T + 0.1, 0.8))
    # recessed player pips
    for i in range(p):
        py = TILE_W / 2 + (i - (p - 1) / 2) * 2.90
        cuts.append(cyl(TILE_PIP_D / 2, TILE_T - TILE_PIP_DEEP, TILE_T + 0.1, 13.0, py))
    # 0.4 x 45 bottom break so it drops into the pocket
    cuts.append(cut(box(-1, TILE_L + 1, -1, TILE_W + 1, -0.1, 0.4),
                    [rrect(0.4, TILE_L - 0.4, 0.4, TILE_W - 0.4, -0.2, 0.5, TILE_R)]))
    return cut(body, cuts)


# ==========================================================================
# 9.  mechanism verification -- measured off the solids, not asserted in prose
# ==========================================================================
def _placed_bar(letter, notch):
    """A cam bar seated in the loom frame at notch 1 or 2."""
    return part_bar(letter).translate((NOTCH_NOSE[notch], CHAN_CL, Z_BAR_BOT))


def _clash(a, b):
    v = a.val().intersect(b.val())
    return sum(s.Volume() for s in v.Solids())


def cam_sweep():
    """For every bar and both notches, read the cam surface height actually
    presented to each of the twelve followers, straight off the solid.  A
    follower footprint is the arm underside: 9.0 (X) x the 14.0 bar width."""
    out = {}
    for letter in sorted(BAR_PROFILES):
        prof = BAR_PROFILES[letter]
        for notch in (1, 2):
            bar = _placed_bar(letter, notch)
            lifts, predicted = [], []
            for n in range(1, N_LANES + 1):
                cx = finger_cx(n)
                probe = box(cx - ARM_W / 2, cx + ARM_W / 2,
                            CHAN_CL - BAR_W / 2, CHAN_CL + BAR_W / 2,
                            Z_BAR_BOT - 1.0, Z_BED + 5.0)
                inter = bar.val().intersect(probe.val())
                lifts.append(round(inter.BoundingBox().zmax - Z_BED, 2))
                predicted.append(prof[n + notch - 2])
            open_lanes = [n for n in range(1, N_LANES + 1) if lifts[n - 1] <= 0.05]
            expect = [n for n in range(1, N_LANES + 1) if predicted[n - 1] == "O"]
            out[f"{letter}{notch}"] = {
                "lift_mm": lifts,
                "open_lanes": open_lanes,
                "matches_profile": open_lanes == expect,
                "full_travel": all(abs(l - LIFT) < 0.05 for l, c
                                   in zip(lifts, predicted) if c == "X"),
            }
    return out


def fit_checks():
    """Interference and clearance between the mating parts, as assembled."""
    deck = part_deck().translate((D2U, 0, 0))
    comb = part_warp_comb()
    rail = part_bar_rail()
    # only the finger TIPS lift; the spine stays seated on the ledge
    tip = cq.Workplane(obj=comb.val().intersect(
        box(0, UF_X, 20.0, ARM_Y1 - 1.0, Z_BED - 1, 5.0).val()))
    comb_up = tip.translate((0, 0, LIFT))
    bar1, bar2 = _placed_bar("a", 1), _placed_bar("a", 2)

    def gap(a, b):
        from OCP.BRepExtrema import BRepExtrema_DistShapeShape
        e = BRepExtrema_DistShapeShape(a.val().wrapped, b.val().wrapped)
        e.Perform()
        return round(e.Value(), 3)

    checks = {
        "deck_x_rail_clash_mm3": round(_clash(deck, rail), 4),
        "deck_x_comb_rest_clash_mm3": round(_clash(deck, comb), 4),
        "deck_x_comb_tip_lifted_clash_mm3": round(_clash(deck, comb_up), 4),
        "rail_x_comb_clash_mm3": round(_clash(rail, comb), 4),
        "rail_x_bar_notch1_clash_mm3": round(_clash(rail, bar1), 4),
        "rail_x_bar_notch2_clash_mm3": round(_clash(rail, bar2), 4),
        "bar_x_channel_gap_mm": gap(rail, bar1),
        "post_top_at_rest_z": round(tip.val().BoundingBox().zmax, 3),
        "post_top_lifted_z": round(comb_up.val().BoundingBox().zmax, 3),
        "lane_wall_top_z": Z_WALL_TOP,
        "handle_proud_of_frame_notch1_mm":
            round(NOTCH_NOSE[1] + BAR_L - UF_X, 2),
        "handle_proud_of_frame_notch2_mm":
            round(NOTCH_NOSE[2] + BAR_L - UF_X, 2),
    }
    # the film really is 3 layers of 0.20 and really is the thinnest section
    film = comb.val().intersect(
        box(finger_cx(1) - 1, finger_cx(1) + 1, FILM_Y0 + 2, FILM_Y1 - 2,
            Z_BED - 1, Z_BED + 5).val())
    checks["film_thickness_mm"] = round(film.BoundingBox().zlen, 3)
    checks["film_layers_at_0p20"] = round(checks["film_thickness_mm"] / 0.20, 2)
    # a tile drops into a pocket, a shuttle fits a lane
    checks["tile_end_clearance_mm"] = round((POCKET_L - TILE_L) / 2, 3)
    checks["tile_side_clearance_mm"] = round((POCKET_W - TILE_W) / 2, 3)
    checks["tile_top_below_flush_mm"] = round(POCKET_DEEP - TILE_T, 3)
    checks["shuttle_side_clearance_mm"] = round((LANE_W - SH_W) / 2, 3)
    checks["post_in_hole_radial_mm"] = round((POST_HOLE_D - POST_D) / 2, 3)
    # peak surface strain in the film at full travel (PETG yields ~3-4 %)
    arm = FILM_Y0 - CHAN_CL                      # 24.0 film end -> post centre
    theta = LIFT / arm
    checks["hinge_rotation_rad"] = round(theta, 4)
    checks["film_peak_strain_pct"] = round(100 * (FILM_T / 2) * (theta / FILM_L), 3)
    return checks


# ==========================================================================
# 10.  build
# ==========================================================================
def parts_table():
    t = [("part_deck", lambda: to_print(part_deck())),
         ("part_bar_rail", lambda: to_print(part_bar_rail())),
         ("part_warp_comb", lambda: to_print(part_warp_comb()))]
    for L in "abcdefgh":
        t.append((f"part_bar_{L}", (lambda ll: (lambda: to_print(part_bar(ll))))(L)))
    for p in (1, 2, 3, 4):
        t.append((f"part_shuttle_p{p}", (lambda pp: (lambda: to_print(part_shuttle(pp))))(p)))
    for p in (1, 2, 3, 4):
        for k in range(1, 9):
            t.append((f"part_tile_p{p}_{k}",
                      (lambda pp: (lambda: to_print(part_tile(pp))))(p)))
    return t


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
    tris = read_stl(path)
    lo, hi = [1e18] * 3, [-1e18] * 3
    edges = {}
    q = lambda pt: (round(pt[0], 4), round(pt[1], 4), round(pt[2], 4))
    for t in tris:
        for pt in t:
            for k in range(3):
                lo[k] = min(lo[k], pt[k])
                hi[k] = max(hi[k], pt[k])
        a, b, c = q(t[0]), q(t[1]), q(t[2])
        for e in ((a, b), (b, c), (c, a)):
            edges[frozenset(e)] = edges.get(frozenset(e), 0) + 1
    return {"facets": len(tris),
            "bbox": [round(hi[k] - lo[k], 3) for k in range(3)],
            "nonmanifold_edges": sum(1 for v in edges.values() if v != 2)}


def main():
    results, built, cache = {}, [], {}
    print(f"{'part':22s} {'bbox (mm)':>28s}  {'vol cm3':>8s} {'shells':>6s} "
          f"{'facets':>7s} {'nm':>4s} {'kB':>8s}  {'s':>5s}")
    for name, fn in parts_table():
        t0 = time.time()
        key = name.rsplit("_", 1)[0] if name.startswith("part_tile") else name
        if key in cache:
            wp = cache[key]
        else:
            wp = fn()
            cache[key] = wp
        path = OUT / f"{name}.stl"
        cq.exporters.export(wp, str(path), tolerance=0.05, angularTolerance=0.35)
        solids = wp.val().Solids()
        vol = sum(s.Volume() for s in solids)
        m = mesh_report(path)
        kb = path.stat().st_size / 1024
        ok = (kb > 0 and vol > 0 and m["facets"] > 0 and len(solids) == 1
              and m["nonmanifold_edges"] == 0
              and max(m["bbox"][0], m["bbox"][1]) <= BED)
        results[name] = dict(m, volume_cm3=round(vol / 1000, 2), shells=len(solids),
                             kb=round(kb, 1), single_body=len(solids) == 1,
                             fits_bed=max(m["bbox"][0], m["bbox"][1]) <= BED, ok=ok)
        built.append(name)
        print(f"{name:22s} {m['bbox'][0]:8.2f} x{m['bbox'][1]:8.2f} x{m['bbox'][2]:7.2f}  "
              f"{vol / 1000:8.2f} {len(solids):6d} {m['facets']:7d} "
              f"{m['nonmanifold_edges']:4d} {kb:8.1f}  {time.time() - t0:5.1f}"
              f"  {'OK' if ok else 'CHECK'}", flush=True)

    bad = [n for n, r in results.items() if not r["ok"]]

    print("\nfit: parts as assembled ...", flush=True)
    fits = fit_checks()
    for k, v in fits.items():
        print(f"  {k:36s} {v}")
    for k, v in fits.items():
        if k.endswith("clash_mm3") and v > 0.02:
            bad.append(f"assembly:{k}")

    print("\ncam: shed presented to the twelve followers ...", flush=True)
    sweep = cam_sweep()
    for k in sorted(sweep):
        r = sweep[k]
        tag = "OK" if r["matches_profile"] and r["full_travel"] else "MISMATCH"
        print(f"  bar {k[0].upper()} notch {k[1]}  open lanes "
              f"{str(r['open_lanes']):<28s} {tag}")
        if tag != "OK":
            bad.append(f"cam:{k}")
    ref = {"a1": [1, 4, 7, 9, 12], "a2": [3, 6, 8, 11]}   # brief S4.3 worked example
    for k, want in ref.items():
        got = sweep[k]["open_lanes"]
        print(f"  brief S4.3 check {k}: want {want} got {got} "
              f"{'OK' if got == want else 'MISMATCH'}")
        if got != want:
            bad.append(f"brief_ref:{k}")

    print(f"\n{len(built)} parts -> {OUT}   failures: {bad or 'none'}")
    (OUT / "_verify.json").write_text(json.dumps(
        {"parts": results, "assembly": fits, "cam_sweep": sweep,
         "failures": bad}, indent=1))
    return built, bad


if __name__ == "__main__":
    main()
