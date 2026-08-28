"""Build123d part constructors for the all-printed Comet Heist game."""

import math
from build123d import Align, Box, Cylinder, GeomType, Pos, Rot, fillet
from params import *
from validation import validate_parameters

validate_parameters()

CENTER_MIN = (Align.CENTER, Align.CENTER, Align.MIN)


def _box(x, y, z, sx, sy, sz):
    return Pos(x, y, z) * Box(sx, sy, sz, align=(Align.CENTER, Align.CENTER, Align.CENTER))


def on_bed(shape, rotation=(0.0, 0.0, 0.0)):
    posed = Rot(*rotation) * shape
    return Pos(0, 0, -posed.bounding_box().min.Z) * posed


def _vault_wall_pips():
    start = -63.8
    lane_centers = (
        start + VAULT_MOUTHS[0] / 2,
        start + VAULT_MOUTHS[0] + VAULT_DIVIDER_T + VAULT_MOUTHS[1] / 2,
        start + VAULT_MOUTHS[0] + VAULT_DIVIDER_T + VAULT_MOUTHS[1] + VAULT_DIVIDER_T + VAULT_MOUTHS[2] / 2,
    )
    pips = []
    for yc, score in zip(lane_centers, VAULT_SCORES):
        cols = 2
        rows = score // 2
        for row in range(rows):
            for col in range(cols):
                pip = Rot(0, 90, 0) * Cylinder(2.0, 2.5, align=CENTER_MIN)
                pips.append(Pos(-94.0, yc + (col - 0.5) * 5.0, 6.0 + row * 5.0) * pip)
    return pips


def _bridge_retaining_shoulders():
    """Integral asymmetric 6 mm slide-lock shoulders at the left tray station."""
    parts = []
    shoulder_z = FLOOR_T + 3.0 + FOOT_VERTICAL_CLEARANCE
    cap_center_z = shoulder_z + RETAINING_SHOULDER_T / 2.0
    post_center_z = (FLOOR_T + shoulder_z + RETAINING_SHOULDER_T) / 2.0
    post_h = shoulder_z + RETAINING_SHOULDER_T - FLOOR_T
    # Both feet lower at X-6 and slide +X. Caps engage only protrusions beyond
    # the 14 mm leg, so the upright never clashes with its retaining shoulder.
    parts.append(_box(62.25, -48.5, post_center_z, 2.0, 12.0, post_h))
    parts.append(_box(60.25, -48.5, cap_center_z, 2.0, 12.0, RETAINING_SHOULDER_T))
    # The +2 mm high-foot offset gets a wider outer capture, enforcing polarity.
    parts.append(_box(64.25, 48.5, post_center_z, 2.0, 12.0, post_h))
    parts.append(_box(61.25, 48.5, cap_center_z, 4.0, 12.0, RETAINING_SHOULDER_T))
    return parts


def build_tray_left():
    # The seam is a true lap: lower half on A, upper half on rotated B.
    floor_main = _box(-1.0, 0, FLOOR_T / 2, TRAY_W - LAP_W, TRAY_D, FLOOR_T)
    floor_lap = _box(102.0, 0, LAP_T / 2, LAP_W, TRAY_D, LAP_T)
    left_wall = _box(-101.6, 0, TRAY_H / 2, WALL_T, TRAY_D, TRAY_H)
    side_low = _box(-1.0, -91.6, TRAY_H / 2, TRAY_W - LAP_W, WALL_T, TRAY_H)
    side_high = _box(-1.0, 91.6, TRAY_H / 2, TRAY_W - LAP_W, WALL_T, TRAY_H)
    lip_low = _box(-1.0, -89.2, TRAY_H - 1.0, TRAY_W - LAP_W, LIP_W, 2.0)
    lip_high = _box(-1.0, 89.2, TRAY_H - 1.0, TRAY_W - LAP_W, LIP_W, 2.0)
    back_wall = _box(-94.4, 0, 10.0, WALL_T, FIELD_D, TRAY_H)
    # Vault mouths: 38 / 50 / 34 mm, separated by 2.8 mm walls.
    div1 = _box(-74.0, -24.4, 6.2, VAULT_DEPTH, VAULT_DIVIDER_T, 7.6)
    div2 = _box(-74.0, 28.4, 6.2, VAULT_DEPTH, VAULT_DIVIDER_T, 7.6)
    # Integral station cheeks leave only the 84 mm central portal.
    cheek_low = _box(52.0, -70.0, FLOOR_T + 4.0, 6.0, 30.0, 8.0)
    cheek_high = _box(52.0, 70.0, FLOOR_T + 4.0, 6.0, 30.0, 8.0)
    # Three tactile ridges mark the one eligible bank facet at this end.
    ridges = []
    for dx in (-15.0, 0.0, 15.0):
        ridge_core = Box(14.0, 4.4, 2.0, align=CENTER_MIN)
        ridge_caps = [Pos(end, 0, 0) * Cylinder(2.2, 2.0, align=CENTER_MIN) for end in (-7.0, 7.0)]
        capsule = ridge_core + ridge_caps
        ridges.append(Pos(-8.0 + dx, -72.0, FLOOR_T - 0.5) * Rot(0, 0, BANK_ANGLE_DEG) * capsule)
    body = floor_main + [floor_lap, left_wall, side_low, side_high, lip_low, lip_high,
                         back_wall, div1, div2, cheek_low, cheek_high, *ridges,
                         *_vault_wall_pips(), *_bridge_retaining_shoulders()]
    # Slot for the magazine's 8 x 3 mm printed tongue.
    slot = _box(-102.0, 0, 11.0, 8.0, 8.6, 9.0)
    return body - slot


def build_tray_right():
    rotated = Rot(0, 0, 180) * build_tray_left()
    lap_region = _box(-102.0, 0, FLOOR_T / 2, LAP_W, TRAY_D, FLOOR_T + 0.2)
    upper_lap = _box(-102.0, 0, FLOOR_T - LAP_T / 2, LAP_W, TRAY_D, LAP_T)
    return (rotated - lap_region) + upper_lap


def build_bridge():
    leg_low = _box(0, -(PORTAL_W + LEG_W) / 2, GATE_H / 2, GATE_DEPTH, LEG_W, GATE_H)
    leg_high = _box(0, (PORTAL_W + LEG_W) / 2, GATE_H / 2, GATE_DEPTH, LEG_W, GATE_H)
    beam = _box(0, 0, GATE_H - 4.5, GATE_DEPTH, PORTAL_W, 9.0)
    # Asymmetric T feet prevent a reversed bridge from seating.
    foot_low = _box(0, -48.5, 1.5, 18.0, 12.0, 3.0)
    foot_high = _box(2.0, 48.5, 1.5, 18.0, 12.0, 3.0)
    bridge = leg_low + [leg_high, beam, foot_low, foot_high]
    bore = Rot(0, 90, 0) * Cylinder(SEAT_D / 2, GATE_DEPTH + 2.0, align=CENTER_MIN)
    bore = Pos(-(GATE_DEPTH + 2.0) / 2, 0, PIVOT_Z - FLOOR_T) * bore
    # Both legs share the coaxial open-seat bore.
    bridge = bridge - [Pos(0, -48.5, 0) * bore, Pos(0, 48.5, 0) * bore]
    # Fixed witnesses and broad stop nubs flank the neutral blade.
    witnesses = [_box(0, y, PIVOT_Z - FLOOR_T, 2.0, 2.4, 10.0) for y in (-41.0, 41.0)]
    return bridge + witnesses


def build_blade():
    arm = _box(0, 0, -11.5, ARM_D, ARM_W, 23.0)
    paddle = _box(0, 0, -PADDLE_RADIUS, PADDLE_D, PADDLE_W, PADDLE_H)
    trunnion = Rot(0, 90, 0) * Cylinder(TRUNNION_D / 2, GATE_DEPTH + 2 * AXIAL_CLEARANCE_EACH, align=CENTER_MIN)
    trunnion = Pos(-(GATE_DEPTH + 2 * AXIAL_CLEARANCE_EACH) / 2, 0, 0) * trunnion
    return arm + [paddle, trunnion]


def build_keeper():
    slab = _box(0, 0, 1.5, 28.0, 10.0, 3.0)
    tab = _box(10.0, 0, 5.0, 8.0, 10.0, 7.0)
    return slab + tab


def build_key():
    bar = _box(0, 0, KEY_T / 2, KEY_L, KEY_W, KEY_T)
    nose = _box(KEY_L / 2 + 3.0, -2.0, KEY_T / 2, 6.0, 8.0, KEY_T)
    hole = Pos(-15.0, 0, -0.5) * Cylinder(2.5, KEY_T + 1.0, align=CENTER_MIN)
    return (bar + nose) - hole


def _comet_base():
    core = Cylinder(COMET_D / 2, COMET_T - COMET_CHAMFER, align=CENTER_MIN)
    top = Pos(0, 0, COMET_T - COMET_CHAMFER) * Cylinder((COMET_D / 2) - COMET_CHAMFER, COMET_CHAMFER, align=CENTER_MIN)
    return core + top


def build_comet_sun():
    comet = _comet_base()
    # A broad filled solar plateau is tactile and avoids sub-nozzle ray tips.
    sun_plateau = Pos(0, 0, COMET_T) * Cylinder(10.0, RELIEF_H, align=CENTER_MIN)
    return comet + sun_plateau


def build_comet_orbit():
    comet = _comet_base()
    outer = Pos(0, 0, COMET_T) * Cylinder(9.0, RELIEF_H, align=CENTER_MIN)
    inner = Pos(0, 0, COMET_T - 0.1) * Cylinder(6.4, RELIEF_H + 0.2, align=CENTER_MIN)
    moon = Pos(9.0, 0, COMET_T) * Cylinder(2.1, RELIEF_H, align=CENTER_MIN)
    return comet + (outer - inner) + moon


def build_magazine():
    body = Box(MAG_W, MAG_D, MAG_H, align=CENTER_MIN)
    wells = [Pos(0, y, MAG_H - MAG_WELL_DEPTH) * Cylinder(MAG_WELL_D / 2, MAG_WELL_DEPTH + 0.5, align=CENTER_MIN) for y in (-18.0, 18.0)]
    body = body - wells
    top_well_rims = [edge for edge in body.edges().filter_by(GeomType.CIRCLE)
                     if abs(edge.bounding_box().min.Z - MAG_H) < 1e-6]
    body = fillet(top_well_rims, radius=0.8)
    tongue = _box(MAG_W / 2 + 3.0, 0, 13.5, 6.0, 8.0, 3.0)
    tongue_web = _box(MAG_W / 2 - 0.5, 0, 11.0, 3.0, 8.0, 8.0)
    # READY has a rising center island; SPENT remains the falling recessed well.
    rising_cue = Pos(0, -18.0, MAG_H - MAG_WELL_DEPTH - 0.5) * Cylinder(4.0, MAG_WELL_DEPTH + 0.5, align=CENTER_MIN)
    return body + [tongue_web, tongue, rising_cue]
