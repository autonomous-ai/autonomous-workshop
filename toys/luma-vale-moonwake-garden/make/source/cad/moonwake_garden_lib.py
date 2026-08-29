"""Parametric geometry for the repaired three-part Moonwake Garden.

All dimensions are millimetres and are bound to sealed Invent round 2.
Each part builder returns its broad rear face on Z=0, the intended print pose.
"""

from __future__ import annotations

import math

try:
    import cadfits
except ModuleNotFoundError:
    # Trusted CAD launchers expose the canonical module.  Host-isolated local
    # audits expose only this copied project, so keep their numerical import
    # path self-contained without depending on a run-root marker.
    import moonwake_fit_fallback as cadfits
from rear_finish import finish_rear
from build123d import (
    Align,
    Box,
    Circle,
    Cylinder,
    Face,
    Location,
    Polygon,
    Pos,
    Rectangle,
    RectangleRounded,
    Rot,
    chamfer,
    extrude,
    fillet,
    loft,
)

Z_MIN_ALIGN = (Align.CENTER, Align.CENTER, Align.MIN)

# Envelope and Z stack [observed: sealed Invent round 2].
FRAME_X = 84.0
FRAME_Y = 76.0
FRAME_CORNER_R = 10.0
ASSEMBLED_Z = 6.0
REAR_PLATE_Z = 1.8
ROTOR_SEAT_Z = 2.1
ROTOR_Z = 1.2
FRONT_SEAT_Z = 3.6
FRONT_PLATE_Z = 1.6
GARDEN_RELIEF_Z = 0.4
MOON_RELIEF_Z = 0.6

# Optical field and repaired rotor/guide stack [observed].
FIELD_D = 64.0
ROTOR_D = 70.0
SPINDLE_D = 6.0
SPINDLE_CLEARANCE_RADIAL = 0.30
ROTOR_BORE_D = cadfits.slot_for(SPINDLE_D, SPINDLE_CLEARANCE_RADIAL)
GUIDE_CLEARANCE_RADIAL = 0.40
GUIDE_ID = cadfits.slot_for(ROTOR_D, GUIDE_CLEARANCE_RADIAL)
GUIDE_WALL = 2.0
GUIDE_OD = GUIDE_ID + 2.0 * GUIDE_WALL
SECTOR_R_IN = 9.0
SECTOR_R_OUT = 31.5
SECTOR_ANGLE_START_DEG = 35.0
SECTOR_ANGLE_END_DEG = 145.0
SECTOR_CORNER_R = 2.0
ROTOR_NORMAL_OUTER_WEB = ROTOR_D / 2.0 - SECTOR_R_OUT

# Rear structure [observed].
HUB_D = 9.0
REAR_STEM_W = 2.4
REAR_STEM_ANGLES_DEG = (30.0, 150.0, 270.0)
THRUST_PAD_RADIAL = 2.0
THRUST_PAD_TANGENTIAL = 4.0
THRUST_PAD_Z = ROTOR_SEAT_Z - REAR_PLATE_Z
THRUST_PAD_R = 31.5
THUMB_BAY_X0 = 31.0
THUMB_BAY_Y = 19.0

# Repaired detent and notch interface [observed].
DETENT_FREE_ANGLE_DEG = -45.0
DETENT_ROOT_ANGLE_DEG = -64.0986
DETENT_CENTER_R = 36.0
DETENT_BEAM_R_IN = 35.4
DETENT_BEAM_R_OUT = 36.6
DETENT_SLOT_R_IN = 36.6
DETENT_SLOT_R_OUT = 37.4
DETENT_FREE_L = 12.0
DETENT_ROOT_FILLET_R = 1.0
DETENT_FREE_CAP = 0.8
DETENT_TOOTH_CENTER_R = 35.4
DETENT_TOOTH_RADIUS = 0.65
DETENT_TOOTH_TIP_R = DETENT_TOOTH_CENTER_R - DETENT_TOOTH_RADIUS
DETENT_NOTCH_DEPTH = 0.55
DETENT_NOTCH_ROOT_R = ROTOR_D / 2.0 - DETENT_NOTCH_DEPTH
DETENT_NOTCH_MOUTH = 2.4
DETENT_NOTCH_ANGLES_DEG = (-45.0, 75.0, 195.0)
MINIMUM_NOTCH_WEB = DETENT_NOTCH_ROOT_R - SECTOR_R_OUT
REQUIRED_OUTER_WEB = 2.5

# Front retention [observed], with female geometry derived from each male.
SNAP_XY = ((-34.0, -27.0), (-34.0, 27.0), (34.0, -27.0), (34.0, 27.0))
COLLAR_D = 5.0
SNAP_STEM_D = 3.2
SNAP_STEM_CLEARANCE_RADIAL = 0.10
SNAP_SPLIT = 0.8
SNAP_HEAD_D = 3.8
SNAP_TIP_D = 2.6
SNAP_LEAD_Z = (SNAP_HEAD_D - SNAP_TIP_D) / 2.0
SNAP_HEAD_LAND_Z = 0.35
SNAP_TIP_Z = 1.0 - SNAP_HEAD_LAND_Z - SNAP_LEAD_Z
SNAP_PRONG_W = 1.0
SNAP_HEAD_PRONG_W = 1.2
SNAP_HOLE_D = cadfits.slot_for(SNAP_STEM_D, SNAP_STEM_CLEARANCE_RADIAL)
SNAP_RELIEF_CLEARANCE_RADIAL = 0.05
SNAP_RELIEF_D = cadfits.slot_for(SNAP_HEAD_D, SNAP_RELIEF_CLEARANCE_RADIAL)
SNAP_RELIEF_DEPTH = 0.5

# Front optical and touch features [observed].
PETAL_L = 4.8
PETAL_W = 2.2
PETAL_ENTRY_CHAMFER = 0.3
VINE_W = 1.2
# Keep the raised vines visually aligned with each petal while ending them as
# printable round caps.  Running a narrow relief through a pointed aperture
# leaves sub-nozzle knife edges at the aperture cusp.
VINE_END_SETBACK = PETAL_L / 2.0 + 0.35
MOON_D = 15.0
PORTAL_R_IN = 32.0
PORTAL_R_OUT = 34.0
PORTAL_ANGLE_START_DEG = -12.0
PORTAL_ANGLE_END_DEG = 12.0
PORTAL_CORNER_R = 0.8
GRIP_CENTER_R = 33.35
GRIP_ANGLES_DEG = (-9.0, -6.0, -3.0, 0.0, 3.0, 6.0, 9.0)
GRIP_TANGENTIAL_L = 1.4
GRIP_RADIAL_W = 0.8
GRIP_DEPTH = 0.3
GRIP_TRENCH_ANGLE_START_DEG = -10.5
GRIP_TRENCH_ANGLE_END_DEG = 10.5
GRIP_TRENCH_CORNER_R = 0.3

PETAL_BEDS = {
    "cassiopeia": ((-16.0, 15.0), (-8.0, 23.0), (0.0, 15.0), (8.0, 23.0), (16.0, 15.0)),
    "cygnus": ((8.0, -23.0), (12.0, -15.0), (16.0, -7.0), (20.0, 1.0), (8.0, -9.0), (24.0, -13.0)),
    "ursa_minor": ((-24.0, -16.0), (-18.0, -21.0), (-11.0, -20.0), (-12.0, -13.0), (-17.0, -8.0), (-20.0, -2.0), (-14.0, 3.0)),
}
ROTOR_STATES_DEG = {"cassiopeia": 0.0, "cygnus": -120.0, "ursa_minor": -240.0}


def validate_parameters() -> None:
    """Fail before geometry if an accepted relationship drifts."""
    assert math.isclose(ROTOR_BORE_D, 6.6)
    assert math.isclose(GUIDE_ID, 70.8)
    assert math.isclose(GUIDE_OD, 74.8)
    assert math.isclose(FRONT_SEAT_Z - (ROTOR_SEAT_Z + ROTOR_Z), 0.30)
    assert math.isclose(ROTOR_NORMAL_OUTER_WEB, 3.50)
    assert math.isclose(DETENT_NOTCH_ROOT_R, 34.45)
    assert math.isclose(MINIMUM_NOTCH_WEB, 2.95)
    assert MINIMUM_NOTCH_WEB >= REQUIRED_OUTER_WEB
    assert math.isclose(DETENT_TOOTH_TIP_R - DETENT_NOTCH_ROOT_R, 0.30)
    assert math.isclose(math.radians(DETENT_FREE_ANGLE_DEG - DETENT_ROOT_ANGLE_DEG) * DETENT_CENTER_R, DETENT_FREE_L, abs_tol=0.001)
    assert math.isclose(FRAME_Y / 2.0 - GUIDE_ID / 2.0, 2.6)
    assert math.isclose(FRAME_Y / 2.0 - GUIDE_OD / 2.0, 0.6)
    assert math.isclose(ROTOR_Z - GRIP_DEPTH, 0.9)
    assert math.isclose(FRONT_SEAT_Z + FRONT_PLATE_Z + MOON_RELIEF_Z, 5.8)
    assert [len(PETAL_BEDS[k]) for k in ROTOR_STATES_DEG] == [5, 6, 7]
    for name, pose in ROTOR_STATES_DEG.items():
        notch = DETENT_NOTCH_ANGLES_DEG[list(ROTOR_STATES_DEG).index(name)]
        assert math.isclose((notch + pose + 180.0) % 360.0 - 180.0, DETENT_FREE_ANGLE_DEG)


def _rounded_plate(height: float):
    return extrude(RectangleRounded(FRAME_X, FRAME_Y, FRAME_CORNER_R), height)


def _polar_xy(radius: float, angle_deg: float) -> tuple[float, float]:
    angle = math.radians(angle_deg)
    return radius * math.cos(angle), radius * math.sin(angle)


def _polar_location(radius: float, angle_deg: float, z: float = 0.0) -> Location:
    return Location((*_polar_xy(radius, angle_deg), z))


def _append_arc(points, center, radius, start_deg, end_deg, steps, clockwise=False):
    if clockwise:
        while end_deg >= start_deg:
            end_deg -= 360.0
    else:
        while end_deg <= start_deg:
            end_deg += 360.0
    for index in range(1, steps + 1):
        angle = start_deg + (end_deg - start_deg) * index / steps
        radians = math.radians(angle)
        points.append((center[0] + radius * math.cos(radians), center[1] + radius * math.sin(radians)))


def _rounded_annular_face(r_in: float, r_out: float, angle_start: float, angle_end: float, fillet_r: float) -> Face:
    """Annular segment with four inward fillets, contained in its polar envelope."""
    outer_delta = math.degrees(math.asin(fillet_r / (r_out - fillet_r)))
    inner_delta = math.degrees(math.asin(fillet_r / (r_in + fillet_r)))
    low_normal = (-math.sin(math.radians(angle_start)), math.cos(math.radians(angle_start)))
    high_normal = (math.sin(math.radians(angle_end)), -math.cos(math.radians(angle_end)))
    centers = {
        "ol": _polar_xy(r_out - fillet_r, angle_start + outer_delta),
        "oh": _polar_xy(r_out - fillet_r, angle_end - outer_delta),
        "il": _polar_xy(r_in + fillet_r, angle_start + inner_delta),
        "ih": _polar_xy(r_in + fillet_r, angle_end - inner_delta),
    }
    tangents = {
        "ol_arc": _polar_xy(r_out, angle_start + outer_delta),
        "oh_arc": _polar_xy(r_out, angle_end - outer_delta),
        "il_arc": _polar_xy(r_in, angle_start + inner_delta),
        "ih_arc": _polar_xy(r_in, angle_end - inner_delta),
        "ol_line": (centers["ol"][0] - fillet_r * low_normal[0], centers["ol"][1] - fillet_r * low_normal[1]),
        "il_line": (centers["il"][0] - fillet_r * low_normal[0], centers["il"][1] - fillet_r * low_normal[1]),
        "oh_line": (centers["oh"][0] - fillet_r * high_normal[0], centers["oh"][1] - fillet_r * high_normal[1]),
        "ih_line": (centers["ih"][0] - fillet_r * high_normal[0], centers["ih"][1] - fillet_r * high_normal[1]),
    }

    def direction(center, point):
        return math.degrees(math.atan2(point[1] - center[1], point[0] - center[0]))

    pts = [tangents["ol_arc"]]
    _append_arc(pts, (0.0, 0.0), r_out, angle_start + outer_delta, angle_end - outer_delta, 48)
    _append_arc(pts, centers["oh"], fillet_r, direction(centers["oh"], tangents["oh_arc"]), direction(centers["oh"], tangents["oh_line"]), 8)
    pts.append(tangents["ih_line"])
    _append_arc(pts, centers["ih"], fillet_r, direction(centers["ih"], tangents["ih_line"]), direction(centers["ih"], tangents["ih_arc"]), 8)
    _append_arc(pts, (0.0, 0.0), r_in, angle_end - inner_delta, angle_start + inner_delta, 48, clockwise=True)
    _append_arc(pts, centers["il"], fillet_r, direction(centers["il"], tangents["il_arc"]), direction(centers["il"], tangents["il_line"]), 8)
    pts.append(tangents["ol_line"])
    _append_arc(pts, centers["ol"], fillet_r, direction(centers["ol"], tangents["ol_line"]), direction(centers["ol"], tangents["ol_arc"]), 8)
    return Polygon(*pts[:-1])


def _annular_face(r_in: float, r_out: float, angle_start: float, angle_end: float, steps: int = 32) -> Face:
    points = [_polar_xy(r_out, angle_start + (angle_end - angle_start) * i / steps) for i in range(steps + 1)]
    points += [_polar_xy(r_in, angle_start + (angle_end - angle_start) * i / steps) for i in range(steps, -1, -1)]
    return Polygon(*points)


def _radial_bar(r0: float, r1: float, width: float, height: float, angle_deg: float, z0: float = 0.0):
    bar = Box(r1 - r0, width, height, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return _polar_location((r0 + r1) / 2.0, angle_deg, z0) * Rot(0, 0, angle_deg) * bar


def _capsule(length: float, width: float) -> Face:
    straight = max(length - width, 0.01)
    return Face.fuse(Rectangle(straight, width), Pos(-straight / 2.0, 0.0) * Circle(width / 2.0), Pos(straight / 2.0, 0.0) * Circle(width / 2.0))


def _lens(length: float, width: float) -> Face:
    radius = (length * length + width * width) / (4.0 * width)
    offset = radius - width / 2.0
    return (Pos(0.0, offset) * Circle(radius)) & (Pos(0.0, -offset) * Circle(radius))


def _notch_tool(angle_deg: float):
    half_angle = math.degrees(math.asin((DETENT_NOTCH_MOUTH / 2.0) / (ROTOR_D / 2.0)))
    apex = _polar_xy(DETENT_NOTCH_ROOT_R, angle_deg)
    lower = _polar_xy(ROTOR_D / 2.0, angle_deg - half_angle)
    upper = _polar_xy(ROTOR_D / 2.0, angle_deg + half_angle)

    def extend(point):
        dx, dy = point[0] - apex[0], point[1] - apex[1]
        scale = 1.0 + 1.0 / math.hypot(dx, dy)
        return apex[0] + dx * scale, apex[1] + dy * scale

    return Pos(0, 0, -0.1) * extrude(Polygon(apex, extend(lower), extend(upper)), ROTOR_Z + 0.2)


def build_sector_rotor():
    validate_parameters()
    rotor = Cylinder(ROTOR_D / 2.0, ROTOR_Z, align=Z_MIN_ALIGN)
    rotor -= Pos(0, 0, -0.1) * Cylinder(ROTOR_BORE_D / 2.0, ROTOR_Z + 0.2, align=Z_MIN_ALIGN)
    sector = _rounded_annular_face(SECTOR_R_IN, SECTOR_R_OUT, SECTOR_ANGLE_START_DEG, SECTOR_ANGLE_END_DEG, SECTOR_CORNER_R)
    rotor -= Pos(0, 0, -0.1) * extrude(sector, ROTOR_Z + 0.2)
    rotor -= [_notch_tool(angle) for angle in DETENT_NOTCH_ANGLES_DEG]
    # The seven sealed capsule footprints overlap one printable continuous
    # control trench.  Leaving each as a separate full-depth opening produces
    # only ~0.35 mm of material between neighbours at this radius.
    grip_trench = _rounded_annular_face(
        GRIP_CENTER_R - GRIP_RADIAL_W / 2.0,
        GRIP_CENTER_R + GRIP_RADIAL_W / 2.0,
        GRIP_TRENCH_ANGLE_START_DEG,
        GRIP_TRENCH_ANGLE_END_DEG,
        GRIP_TRENCH_CORNER_R,
    )
    rotor -= Pos(0, 0, ROTOR_Z - GRIP_DEPTH) * extrude(grip_trench, GRIP_DEPTH + 0.01)
    rotor.label = "sector_rotor:print_pose"
    return rotor


def _rear_bay_tool(z0: float, height: float):
    half_angle = math.degrees(math.asin((THUMB_BAY_Y / 2.0) / (GUIDE_ID / 2.0)))
    # A polar throat intersects every circular guide boundary transversely.
    # A Cartesian rectangle would meet the guide almost tangentially at
    # y=+/-9.5 and create sub-nozzle wedges.
    bay = _annular_face(THUMB_BAY_X0, FRAME_X, -half_angle, half_angle)
    return Pos(0, 0, z0) * extrude(bay, height)


def _detent_beam_and_tooth():
    beam = extrude(_annular_face(DETENT_BEAM_R_IN, DETENT_BEAM_R_OUT, DETENT_ROOT_ANGLE_DEG, DETENT_FREE_ANGLE_DEG), FRONT_SEAT_Z)
    root = _polar_location(DETENT_CENTER_R, DETENT_ROOT_ANGLE_DEG) * Cylinder(DETENT_ROOT_FILLET_R, FRONT_SEAT_Z, align=Z_MIN_ALIGN)
    tooth = _polar_location(DETENT_TOOTH_CENTER_R, DETENT_FREE_ANGLE_DEG) * Cylinder(DETENT_TOOTH_RADIUS, FRONT_SEAT_Z, align=Z_MIN_ALIGN)
    return beam + root + tooth


def _spindle_with_root_fillet():
    spindle = Cylinder(SPINDLE_D / 2.0, FRONT_SEAT_Z, align=Z_MIN_ALIGN)
    sections = []
    for i in range(9):
        z = REAR_PLATE_Z + i * 1.0 / 8.0
        radius = SPINDLE_D / 2.0 + 1.0 - math.sqrt(max(0.0, 1.0 - (z - (REAR_PLATE_Z + 1.0)) ** 2))
        sections.append(Pos(0, 0, z) * Circle(radius))
    return spindle + loft(sections, ruled=True)


def _snap_prong_profile(outer_x: float, width: float, side: float):
    """Blunt round-cornered prong wholly inside its diameter envelope."""
    inner_x = SNAP_SPLIT / 2.0
    length = outer_x - inner_x
    center_x = side * (inner_x + outer_x) / 2.0
    return Pos(center_x, 0.0) * RectangleRounded(length, width, 0.1)


def _snap_post(x: float, y: float):
    local_collar = Cylinder(COLLAR_D / 2.0, FRONT_SEAT_Z, align=Z_MIN_ALIGN)
    collar_top = [edge for edge in local_collar.edges() if abs(edge.center().Z - FRONT_SEAT_Z) < 0.01]
    local_collar = fillet(collar_top, 0.4)
    collar = Pos(x, y, 0) * local_collar
    prongs = []
    head_cap_x = math.sqrt((SNAP_HEAD_D / 2.0) ** 2 - (SNAP_HEAD_PRONG_W / 2.0 - 0.1) ** 2) - 0.01
    for side in (-1.0, 1.0):
        stem_profile = _snap_prong_profile(SNAP_STEM_D / 2.0, SNAP_PRONG_W, side)
        stem = Pos(x, y, FRONT_SEAT_Z) * extrude(stem_profile, 1.1)
        head_sections = [
            Pos(x, y, 4.7) * _snap_prong_profile(SNAP_STEM_D / 2.0, SNAP_PRONG_W, side),
            Pos(x, y, 4.8) * _snap_prong_profile(SNAP_STEM_D / 2.0, SNAP_HEAD_PRONG_W, side),
            Pos(x, y, 5.0) * _snap_prong_profile(head_cap_x, SNAP_HEAD_PRONG_W, side),
            Pos(x, y, 5.0 + SNAP_HEAD_LAND_Z) * _snap_prong_profile(head_cap_x, SNAP_HEAD_PRONG_W, side),
            Pos(x, y, 5.0 + SNAP_HEAD_LAND_Z + SNAP_LEAD_Z) * _snap_prong_profile(SNAP_TIP_D / 2.0, SNAP_PRONG_W, side),
            Pos(x, y, ASSEMBLED_Z) * _snap_prong_profile(SNAP_TIP_D / 2.0, SNAP_PRONG_W, side),
        ]
        prongs.append(stem + loft(head_sections, ruled=True))
    return collar + prongs


def build_rear_chassis():
    validate_parameters()
    rear = _rounded_plate(REAR_PLATE_Z) - Pos(0, 0, -0.1) * Cylinder(FIELD_D / 2.0, REAR_PLATE_Z + 0.2, align=Z_MIN_ALIGN)
    rear += Cylinder(HUB_D / 2.0, REAR_PLATE_Z, align=Z_MIN_ALIGN)
    # Carry each spoke well into the base annulus.  A merely 0.8 mm radial
    # overlap leaves tangential cusp slivers where a spoke meets the R32 field.
    rear += [_radial_bar(HUB_D / 2.0 - 0.2, FIELD_D / 2.0 + 2.0, REAR_STEM_W, REAR_PLATE_Z, angle) for angle in REAR_STEM_ANGLES_DEG]
    guide = Pos(0, 0, REAR_PLATE_Z) * (Cylinder(GUIDE_OD / 2.0, FRONT_SEAT_Z - REAR_PLATE_Z, align=Z_MIN_ALIGN) - Cylinder(GUIDE_ID / 2.0, FRONT_SEAT_Z - REAR_PLATE_Z, align=Z_MIN_ALIGN))
    rear += guide
    rear -= _rear_bay_tool(-0.1, FRONT_SEAT_Z + 0.2)

    outer_slot = Pos(0, 0, -0.1) * extrude(_annular_face(DETENT_SLOT_R_IN, DETENT_SLOT_R_OUT + 0.2, DETENT_ROOT_ANGLE_DEG, DETENT_FREE_ANGLE_DEG), FRONT_SEAT_Z + 0.2)
    # Clear the base through the beam's outer face, then add the beam back as
    # the sole material across the free arc.  Stopping at its inner face would
    # leave the rejected plate bridge beneath the flexure.
    underbeam = Pos(0, 0, -0.1) * extrude(_annular_face(FIELD_D / 2.0 - 0.1, DETENT_BEAM_R_OUT, DETENT_ROOT_ANGLE_DEG, DETENT_FREE_ANGLE_DEG), REAR_PLATE_Z + 0.2)
    cap_r0 = DETENT_BEAM_R_IN - 0.2
    cap_r1 = DETENT_SLOT_R_OUT + 0.2
    cap_angle_deg = math.degrees(DETENT_FREE_CAP / DETENT_CENTER_R)
    free_cap = Pos(0, 0, -0.1) * extrude(
        _annular_face(
            cap_r0,
            cap_r1,
            DETENT_FREE_ANGLE_DEG,
            DETENT_FREE_ANGLE_DEG + cap_angle_deg,
        ),
        FRONT_SEAT_Z + 0.2,
    )
    rear -= [outer_slot, underbeam, free_cap]
    rear += _detent_beam_and_tooth()
    rear += _spindle_with_root_fillet()

    for angle in REAR_STEM_ANGLES_DEG:
        # The full 2 x 4 pad footprint needs base material beneath it.  Without
        # this local support, its tangential wings are only 0.3 mm membranes
        # over the open optical field.
        support = Cylinder(2.4, REAR_PLATE_Z, align=Z_MIN_ALIGN)
        rear += _polar_location(THRUST_PAD_R, angle, 0.0) * support
        pad = extrude(RectangleRounded(THRUST_PAD_RADIAL, THRUST_PAD_TANGENTIAL, 0.4), THRUST_PAD_Z)
        rear += _polar_location(THRUST_PAD_R, angle, REAR_PLATE_Z) * Rot(0, 0, angle) * pad
    rear += [_snap_post(x, y) for x, y in SNAP_XY]

    # Round the polar bay breakthroughs and vertical detent endpoint edges
    # before the final axial-rim chamfers.
    bay_half_angle = math.degrees(math.asin((THUMB_BAY_Y / 2.0) / (GUIDE_ID / 2.0)))
    edge_repairs = [
        *[
            (_polar_xy(radius, angle), 0.4)
            for radius in (FIELD_D / 2.0, GUIDE_ID / 2.0, GUIDE_OD / 2.0)
            for angle in (-bay_half_angle, bay_half_angle)
        ],
        (_polar_xy(DETENT_SLOT_R_OUT, DETENT_ROOT_ANGLE_DEG), 0.3),
        (_polar_xy(DETENT_BEAM_R_OUT, DETENT_FREE_ANGLE_DEG), 0.4),
        *[
            (_polar_xy(radius, DETENT_FREE_ANGLE_DEG + cap_angle_deg), 0.4)
            for radius in (DETENT_BEAM_R_IN, DETENT_SLOT_R_OUT)
        ],
    ]
    for (target_x, target_y), radius in edge_repairs:
        edges = [
            edge
            for edge in rear.edges()
            if abs(edge.tangent_at(0.5).Z) > 0.99
            and math.hypot(edge.center().X - target_x, edge.center().Y - target_y) < 0.18
        ]
        if not edges:
            # An earlier axial-rim fillet can consume this corner completely.
            continue
        edge = min(
            edges,
            key=lambda candidate: (
                math.hypot(candidate.center().X - target_x, candidate.center().Y - target_y),
                -candidate.length,
            ),
        )
        rear = fillet([edge], radius)

    rear = finish_rear(
        rear,
        field_d=FIELD_D,
        guide_id=GUIDE_ID,
        front_z=FRONT_SEAT_Z,
        rear_z=REAR_PLATE_Z,
        root_angle=DETENT_ROOT_ANGLE_DEG,
        free_angle=DETENT_FREE_ANGLE_DEG,
        slot_r=DETENT_SLOT_R_OUT,
    )
    rear.label = "rear_chassis:print_pose"
    return rear


def _vine_relief():
    reliefs = []
    for points in PETAL_BEDS.values():
        for p0, p1 in zip(points[:-1], points[1:]):
            dx, dy = p1[0] - p0[0], p1[1] - p0[1]
            length = math.hypot(dx, dy)
            angle = math.degrees(math.atan2(dy, dx))
            printable_length = length - 2.0 * VINE_END_SETBACK
            if printable_length <= 0.0:
                raise ValueError("petal spacing is too short for a printable vine segment")
            reliefs.append(
                Pos(
                    (p0[0] + p1[0]) / 2.0,
                    (p0[1] + p1[1]) / 2.0,
                    FRONT_PLATE_Z,
                )
                * Rot(0, 0, angle)
                * extrude(_capsule(printable_length, VINE_W), GARDEN_RELIEF_Z)
            )
    return reliefs


def _petal_cutters():
    cutters = []
    for points in PETAL_BEDS.values():
        for x, y in points:
            angle = math.degrees(math.atan2(y, x))
            nominal = _lens(PETAL_L, PETAL_W)
            rear = _lens(PETAL_L + 2.0 * PETAL_ENTRY_CHAMFER, PETAL_W + 2.0 * PETAL_ENTRY_CHAMFER)
            chamfer = loft((Pos(0, 0, -0.1) * rear, Pos(0, 0, PETAL_ENTRY_CHAMFER) * nominal), ruled=True)
            through = Pos(0, 0, PETAL_ENTRY_CHAMFER - 0.01) * extrude(nominal, FRONT_PLATE_Z + MOON_RELIEF_Z)
            cutters.append(Pos(x, y, 0) * Rot(0, 0, angle) * (chamfer + through))
    return cutters


def build_front_garden_mask():
    validate_parameters()
    face = _rounded_plate(FRONT_PLATE_Z)
    face += _vine_relief()
    face += Pos(0, 0, FRONT_PLATE_Z) * Cylinder(MOON_D / 2.0, MOON_RELIEF_Z, align=Z_MIN_ALIGN)
    face -= _petal_cutters()
    portal = _rounded_annular_face(PORTAL_R_IN, PORTAL_R_OUT, PORTAL_ANGLE_START_DEG, PORTAL_ANGLE_END_DEG, PORTAL_CORNER_R)
    face -= Pos(0, 0, -0.1) * extrude(portal, FRONT_PLATE_Z + MOON_RELIEF_Z + 0.2)
    for x, y in SNAP_XY:
        face -= Pos(x, y, -0.1) * Cylinder(SNAP_HOLE_D / 2.0, FRONT_PLATE_Z + 0.2, align=Z_MIN_ALIGN)
        face -= Pos(x, y, FRONT_PLATE_Z - SNAP_RELIEF_DEPTH) * Cylinder(SNAP_RELIEF_D / 2.0, SNAP_RELIEF_DEPTH + 0.1, align=Z_MIN_ALIGN)
    face.label = "front_garden_mask:print_pose"
    return face


validate_parameters()
