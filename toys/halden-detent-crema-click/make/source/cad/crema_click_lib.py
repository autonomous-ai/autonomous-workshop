"""Crema Click — weighted demitasse desk clicker.

Origin: foot centre on the desk plane. +Z up. +X through the handle.
Units: millimetres. Journal and well mates derive through cadfits.
"""

from __future__ import annotations

import math

import cadfits
from build123d import (
    Align,
    Axis,
    Box,
    BuildLine,
    BuildSketch,
    Cone,
    Cylinder,
    Location,
    Mode,
    Plane,
    Polygon,
    Polyline,
    Pos,
    Rot,
    extrude,
    make_face,
    revolve,
)
from cadfilament import filament
from cadgen.assembly import AssemblyHelper

ZMIN = (Align.CENTER, Align.CENTER, Align.MIN)

# Envelope [assumed]
RIM_OD = 64.0
RIM_ID = 47.2
FOOT_OD = 56.0
OBJECT_H = 50.0
PLUG_H = 5.5
WALL = 2.4
HANDLE_PROJ = 22.0

MOUTH_R = RIM_ID / 2.0
RIM_R = RIM_OD / 2.0
FOOT_R = FOOT_OD / 2.0

CHIMNEY_ID = 16.80  # female journal [assumed]
STEM_OD = cadfits.peg_for(CHIMNEY_ID, "slip")
LIP_RADIAL = 2.4
LIP_ID = CHIMNEY_ID - 2 * LIP_RADIAL
NECK_OD = cadfits.peg_for(LIP_ID, "slip")
FLANGE_OD = LIP_ID + 1.20
TRAVEL = 4.5
CREST = 2.8
CLICK_DROP = 0.45
DIMPLE = 0.80
DISC_OD = 44.0
DISC_H = 5.0
DISC_PROUD = 4.0
MAG_D = 8.0
MAG_H = 3.0
MAG_FLOOR = 1.2
BIAS_D = 6.0
BIAS_H = 2.0
DETENT_BALL_D = 4.00
BALLAST_D = 10.00
WELL_ID = cadfits.slot_for(BALLAST_D, "snug")
CAGE_ID = cadfits.slot_for(DETENT_BALL_D, "slip")
WINDOW_ID = 3.70
BALLAST_PITCH = 38.0
BALLAST_COUNT = 4
WELL_DEPTH = BALLAST_D + 0.20
MAG_POCKET_D = cadfits.slot_for(MAG_D, "slip")
BIAS_POCKET_D = cadfits.slot_for(BIAS_D, "slip")

# Foot capture: three inward lugs; ramps stay inside the lug ID until
# they clear the lug top, then flare out so seated pose does not clash.
LUG_COUNT = 3
LUG_W = 12.0
LUG_RADIAL = 2.4
LUG_H = 2.2
LUG_LOCK_DEG = 0.0
LUG_ENTRY_DEG = 60.0
TAB_W = 10.0
TAB_POST_W = 2.4
TAB_CLEAR_Z = 0.30
TAB_FLARE_H = 2.6
LEDGE_DEG = 40.0

CUP_COLOR = filament("cocoa brown")
PLUG_COLOR = CUP_COLOR
PISTON_COLOR = filament("beige")

RIM_Z = OBJECT_H
DISC_TOP_HOME = RIM_Z + DISC_PROUD
DISC_BACK_HOME = DISC_TOP_HOME - DISC_H
LIP_Z = 40.0
PLUG_TOP = PLUG_H
STEM_R = STEM_OD / 2.0
NECK_R = NECK_OD / 2.0
FLANGE_R = FLANGE_OD / 2.0

POLE_GAP_HOME = 7.0
FLOOR_MAG_Z0 = PLUG_TOP + 0.8
FLOOR_MAG_FACE = FLOOR_MAG_Z0 + MAG_H
PISTON_MAG_FACE = FLOOR_MAG_FACE + POLE_GAP_HOME
STEM_LEN = DISC_BACK_HOME - (PISTON_MAG_FACE - MAG_FLOOR)
BALL_Z = 23.0
FLANGE_Z0 = 32.0
FLANGE_H = 1.6

# Lugs live on the inner foot ring, clear of ballast wells on a 45 deg pitch.
LUG_INNER_R = 23.2
LUG_R = LUG_INNER_R + LUG_RADIAL / 2.0
TAB_INNER_R = 20.4
TAB_POST_OUTER_R = TAB_INNER_R + TAB_POST_W

assert math.isclose(STEM_OD, 16.40, abs_tol=1e-9)
assert math.isclose(WELL_ID, 10.20, abs_tol=1e-9)
assert math.isclose(CAGE_ID, 4.40, abs_tol=1e-9)
assert math.isclose(LIP_ID, 12.00, abs_tol=1e-9)
assert math.isclose(NECK_OD, 11.60, abs_tol=1e-9)
assert math.isclose(FLANGE_OD, 13.20, abs_tol=1e-9)
assert STEM_LEN > 22.0
assert FLANGE_Z0 + FLANGE_H < LIP_Z
assert DISC_BACK_HOME - TRAVEL > LIP_Z
assert BALL_Z > FLOOR_MAG_FACE + 6.0
assert TAB_POST_OUTER_R < LUG_INNER_R - 0.3
assert LUG_INNER_R + LUG_RADIAL < FOOT_R - 0.8
assert LUG_H + TAB_CLEAR_Z + TAB_FLARE_H < 8.0


def _profile_face(pts):
    with BuildSketch(Plane.XZ) as sk:
        with BuildLine():
            Polyline(*pts, close=True)
        make_face()
    return sk.sketch


def _handle():
    """C-handle spanning most of the cup height. Inner hole is a triangle
    pointing at the rim so the roof prints as a point when foot-down."""
    outer_w = 16.0
    outer_h = 38.0
    hw, hh = outer_w / 2.0, outer_h / 2.0
    with BuildSketch(Plane.XZ) as sk:
        Polygon(
            (-hw, -hh),
            (hw, -hh),
            (hw, hh - 6.0),
            (hw - 5.0, hh),
            (-hw + 3.0, hh),
            (-hw, hh - 4.0),
        )
        with BuildLine():
            Polyline((-4.5, -11.0), (4.5, -11.0), (0.0, 12.0), close=True)
        make_face(mode=Mode.SUBTRACT)
    bar = extrude(sk.sketch, amount=8.0, dir=(0, 1, 0))
    bar = Pos(0, -4.0, 0) * bar
    # Inner edge overlaps the cup wall so the handle is fused, not floating.
    cx = RIM_R - 2.0 + outer_w / 2.0
    cz = PLUG_TOP + outer_h / 2.0
    return Pos(cx, 0, cz) * bar


def _lug_solid():
    """Rectangular shelf on the cup foot plane so it prints on the bed."""
    return Pos(LUG_R, 0, PLUG_TOP) * Box(
        LUG_RADIAL, LUG_W, LUG_H, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )


def _tab_solid():
    """Vertical post inside the lug ID, then a 40 deg flare over the lug top."""
    z_clear = LUG_H + TAB_CLEAR_Z
    lip = 1.2
    slope_h = TAB_FLARE_H - lip
    z_top = z_clear + TAB_FLARE_H
    flare = slope_h * math.tan(math.radians(LEDGE_DEG))
    post = TAB_POST_W
    pts = [
        (0.0, 0.0),
        (post, 0.0),
        (post, z_clear),
        (post + flare, z_clear + slope_h),
        (post + flare, z_top),
        (0.0, z_top),
    ]
    face = _profile_face(pts)
    bar = extrude(face, amount=TAB_W, dir=(0, 1, 0))
    bar = Pos(0, -TAB_W / 2.0, 0) * bar
    return Pos(TAB_INNER_R, 0, PLUG_TOP) * bar


def _entry_window():
    """Chunky slot at the cup foot so the post and flare can enter."""
    h = LUG_H + TAB_CLEAR_Z + TAB_FLARE_H + 0.8
    w = TAB_W + 1.6
    radial = TAB_POST_W + TAB_FLARE_H * math.tan(math.radians(LEDGE_DEG)) + 1.2
    return Pos(TAB_INNER_R + radial / 2.0, 0, PLUG_TOP - 0.3) * Box(
        radial, w, h, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )


def build_cup_body():
    """Demitasse, handle, chimney, cages, wells, capture lugs."""
    pts = [
        (0.0, PLUG_TOP),
        (FOOT_R, PLUG_TOP),
        (FOOT_R, PLUG_TOP + 3.0),
        (FOOT_R + 0.6, PLUG_TOP + 6.0),
        (RIM_R - 2.4, 22.0),
        (RIM_R - 0.6, 38.0),
        (RIM_R, RIM_Z - 2.0),
        (RIM_R - 1.4, RIM_Z),
        (0.0, RIM_Z),
    ]
    body = revolve(_profile_face(pts), Axis.Z)

    cuts = []
    cuts.append(Pos(0, 0, LIP_Z) * Cylinder(MOUTH_R, RIM_Z - LIP_Z + 0.4, align=ZMIN))
    lip_taper = LIP_RADIAL / math.tan(math.radians(38.0))
    lip_straight = 2.4
    cone_over = 0.4
    cone_z0 = LIP_Z - lip_taper - lip_straight - cone_over
    cone_r0 = CHIMNEY_ID / 2.0 + cone_over * math.tan(math.radians(38.0))
    chimney_top = LIP_Z - lip_taper - lip_straight
    cuts.append(
        Pos(0, 0, PLUG_TOP - 0.2)
        * Cylinder(CHIMNEY_ID / 2.0, chimney_top - (PLUG_TOP - 0.2), align=ZMIN)
    )
    cuts.append(
        Pos(0, 0, cone_z0)
        * Cone(cone_r0, LIP_ID / 2.0, lip_taper + cone_over + 0.15, align=ZMIN)
    )
    cuts.append(
        Pos(0, 0, LIP_Z - lip_straight)
        * Cylinder(LIP_ID / 2.0, lip_straight + 0.3, align=ZMIN)
    )
    cuts.append(
        Pos(0, 0, FLOOR_MAG_Z0 - 0.15)
        * Cylinder(MAG_POCKET_D / 2.0, MAG_H + 0.5, align=ZMIN)
    )
    well_r = BALLAST_PITCH / 2.0
    for i in range(BALLAST_COUNT):
        ang = math.radians(45.0 + i * 90.0)
        x, y = well_r * math.cos(ang), well_r * math.sin(ang)
        cuts.append(
            Pos(x, y, PLUG_TOP - 0.2)
            * Cylinder(WELL_ID / 2.0, WELL_DEPTH + 0.4, align=ZMIN)
        )
    for ang_deg in (90.0, 270.0):
        ca = math.radians(ang_deg)
        drop_r = 14.2
        dx, dy = drop_r * math.cos(ca), drop_r * math.sin(ca)
        cuts.append(
            Pos(dx, dy, PLUG_TOP - 0.2)
            * Cylinder(CAGE_ID / 2.0, BALL_Z - PLUG_TOP + 2.6, align=ZMIN)
        )
        cuts.append(
            Pos(0, 0, BALL_Z)
            * Rot(0, 0, ang_deg)
            * Pos(CHIMNEY_ID / 2.0 - 1.2, 0, 0)
            * Rot(0, 90, 0)
            * Cylinder(CAGE_ID / 2.0, 8.5, align=ZMIN)
        )
        cuts.append(
            Pos(0, 0, BALL_Z)
            * Rot(0, 0, ang_deg)
            * Pos(CHIMNEY_ID / 2.0 - 2.0, 0, 0)
            * Rot(0, 90, 0)
            * Cylinder(WINDOW_ID / 2.0, 5.0, align=ZMIN)
        )
        mx, my = 17.2 * math.cos(ca), 17.2 * math.sin(ca)
        cuts.append(
            Pos(mx, my, BALL_Z - BIAS_H / 2.0 - 0.15)
            * Cylinder(BIAS_POCKET_D / 2.0, BIAS_H + 0.4, align=ZMIN)
        )
    # Entry windows so the ramps pass the lugs on the way in.
    for i in range(LUG_COUNT):
        cuts.append(Rot(0, 0, i * 120.0 + LUG_ENTRY_DEG) * _entry_window())
    # Locked-pose pockets: seated ramps occupy this volume; lugs are added back.
    for i in range(LUG_COUNT):
        cuts.append(Rot(0, 0, i * 120.0 + LUG_LOCK_DEG) * _tab_solid())

    body -= cuts
    for i in range(LUG_COUNT):
        body += Rot(0, 0, i * 120.0 + LUG_LOCK_DEG) * _lug_solid()
    body += _handle()
    body.label = "cup_body"
    body.color = CUP_COLOR
    return body


def _piston_local_home_z():
    return DISC_TOP_HOME - BALL_Z


def build_crema_piston():
    """Disc, neck, flange, ramp stem, magnet well. Local: thumb at Z=0."""
    z_home = _piston_local_home_z()
    z_crest = z_home - CREST
    z_valley = z_crest - CLICK_DROP
    z_bottom = z_home - TRAVEL
    flange_local = DISC_TOP_HOME - (FLANGE_Z0 + FLANGE_H)
    tip = DISC_H + STEM_LEN

    flange_run = FLANGE_R - NECK_R
    flange_rise = flange_run / math.tan(math.radians(38.0))
    stem_rise = (STEM_R - NECK_R) / math.tan(math.radians(38.0))
    after_flange = flange_local + FLANGE_H + flange_rise
    pts = [
        (0.0, 0.0),
        (DISC_OD / 2.0 - 0.8, 0.0),
        (DISC_OD / 2.0, 0.8),
        (DISC_OD / 2.0, DISC_H),
        (NECK_R, DISC_H),
        (NECK_R, flange_local),
        (FLANGE_R, flange_local + flange_rise),
        (FLANGE_R, flange_local + FLANGE_H),
        (NECK_R, after_flange),
        (STEM_R, after_flange + stem_rise),
        (STEM_R, z_bottom),
        (STEM_R - 0.40, z_valley),
        (STEM_R, z_crest),
        (STEM_R - DIMPLE, z_home),
        (STEM_R, z_home + 2.4),
        (STEM_R, tip),
        (0.0, tip),
    ]
    part = revolve(_profile_face(pts), Axis.Z)
    well_z = tip - MAG_FLOOR - MAG_H
    part -= Pos(0, 0, well_z) * Cylinder(MAG_POCKET_D / 2.0, MAG_H + 0.08, align=ZMIN)
    part -= Pos(0, 0, tip - MAG_FLOOR - 0.05) * Cylinder(3.4, MAG_FLOOR + 0.3, align=ZMIN)
    part.label = "crema_piston"
    part.color = PISTON_COLOR
    return part


def piston_world_location(travel: float = 0.0) -> Location:
    return Pos(0, 0, DISC_TOP_HOME - travel) * Rot(180, 0, 0)


def build_foot_plug():
    """Desk face, magnet-boss, three capture lips at the locked angle."""
    plug = Cylinder(FOOT_R, PLUG_H, align=ZMIN)
    for i in range(LUG_COUNT):
        plug += Rot(0, 0, i * 120.0 + LUG_LOCK_DEG) * _tab_solid()
    boss_h = FLOOR_MAG_Z0 - PLUG_H + 0.35
    plug += Pos(0, 0, PLUG_H) * Cylinder(MAG_POCKET_D / 2.0 + 1.5, boss_h, align=ZMIN)
    plug -= Pos(0, 0, PLUG_H) * Cylinder(MAG_POCKET_D / 2.0, boss_h + 0.25, align=ZMIN)
    plug.label = "foot_plug"
    plug.color = PLUG_COLOR
    return plug


def placed_piston(travel: float = 0.0):
    return piston_world_location(travel) * build_crema_piston()


def build_assembly(travel: float = 0.0):
    asm = AssemblyHelper("crema_click")
    cup = asm.add(build_cup_body(), "cup_body", color=CUP_COLOR)
    piston = asm.add(placed_piston(travel), "crema_piston", color=PISTON_COLOR)
    asm.add(build_foot_plug(), "foot_plug", color=PLUG_COLOR)
    asm.linear_frame(cup, "chimney_axis", Axis.Z)
    asm.linear_frame(piston, "stem_axis", Axis.Z)
    return asm


def assembled(travel: float = 0.0):
    return build_assembly(travel).build()
