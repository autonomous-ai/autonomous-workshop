"""Independent algebraic and planar audit for Moonwake Garden Make round 2."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

HERE = Path(__file__).resolve()
PROJECT = HERE.parents[1]
sys.path.insert(0, str(PROJECT))

import moonwake_garden_lib as m  # noqa: E402

EPS_AREA = 0.001


def polar(radius: float, angle_deg: float) -> tuple[float, float]:
    angle = math.radians(angle_deg)
    return radius * math.cos(angle), radius * math.sin(angle)


def append_arc(points, center, radius, start_deg, end_deg, steps, clockwise=False):
    if clockwise:
        while end_deg >= start_deg:
            end_deg -= 360.0
    else:
        while end_deg <= start_deg:
            end_deg += 360.0
    for index in range(1, steps + 1):
        angle = math.radians(start_deg + (end_deg - start_deg) * index / steps)
        points.append((center[0] + radius * math.cos(angle), center[1] + radius * math.sin(angle)))


def rounded_annular_segment(r_in, r_out, angle_start, angle_end, fillet_r):
    outer_delta = math.degrees(math.asin(fillet_r / (r_out - fillet_r)))
    inner_delta = math.degrees(math.asin(fillet_r / (r_in + fillet_r)))
    low_normal = (-math.sin(math.radians(angle_start)), math.cos(math.radians(angle_start)))
    high_normal = (math.sin(math.radians(angle_end)), -math.cos(math.radians(angle_end)))
    centers = {
        "ol": polar(r_out - fillet_r, angle_start + outer_delta),
        "oh": polar(r_out - fillet_r, angle_end - outer_delta),
        "il": polar(r_in + fillet_r, angle_start + inner_delta),
        "ih": polar(r_in + fillet_r, angle_end - inner_delta),
    }
    tangents = {
        "ol_arc": polar(r_out, angle_start + outer_delta),
        "oh_arc": polar(r_out, angle_end - outer_delta),
        "il_arc": polar(r_in, angle_start + inner_delta),
        "ih_arc": polar(r_in, angle_end - inner_delta),
        "ol_line": (centers["ol"][0] - fillet_r * low_normal[0], centers["ol"][1] - fillet_r * low_normal[1]),
        "il_line": (centers["il"][0] - fillet_r * low_normal[0], centers["il"][1] - fillet_r * low_normal[1]),
        "oh_line": (centers["oh"][0] - fillet_r * high_normal[0], centers["oh"][1] - fillet_r * high_normal[1]),
        "ih_line": (centers["ih"][0] - fillet_r * high_normal[0], centers["ih"][1] - fillet_r * high_normal[1]),
    }

    def direction(center, point):
        return math.degrees(math.atan2(point[1] - center[1], point[0] - center[0]))

    points = [tangents["ol_arc"]]
    append_arc(points, (0, 0), r_out, angle_start + outer_delta, angle_end - outer_delta, 256)
    append_arc(points, centers["oh"], fillet_r, direction(centers["oh"], tangents["oh_arc"]), direction(centers["oh"], tangents["oh_line"]), 32)
    points.append(tangents["ih_line"])
    append_arc(points, centers["ih"], fillet_r, direction(centers["ih"], tangents["ih_line"]), direction(centers["ih"], tangents["ih_arc"]), 32)
    append_arc(points, (0, 0), r_in, angle_end - inner_delta, angle_start + inner_delta, 256, clockwise=True)
    append_arc(points, centers["il"], fillet_r, direction(centers["il"], tangents["il_arc"]), direction(centers["il"], tangents["il_line"]), 32)
    points.append(tangents["ol_line"])
    append_arc(points, centers["ol"], fillet_r, direction(centers["ol"], tangents["ol_line"]), direction(centers["ol"], tangents["ol_arc"]), 32)
    return Polygon(points)


def raw_annular_segment(r_in, r_out, angle_start, angle_end):
    points = [polar(r_out, angle_start + (angle_end - angle_start) * i / 512) for i in range(513)]
    points += [polar(r_in, angle_start + (angle_end - angle_start) * i / 512) for i in range(512, -1, -1)]
    return Polygon(points)


def lens(length, width):
    radius = (length * length + width * width) / (4.0 * width)
    offset = radius - width / 2.0
    return Point(0, offset).buffer(radius, resolution=256).intersection(Point(0, -offset).buffer(radius, resolution=256))


def place_radial(shape, xy):
    x, y = xy
    rotated = affinity.rotate(shape, math.degrees(math.atan2(y, x)), origin=(0, 0))
    return affinity.translate(rotated, x, y)


def notch_triangle(angle_deg):
    half_angle = math.degrees(math.asin((m.DETENT_NOTCH_MOUTH / 2.0) / (m.ROTOR_D / 2.0)))
    return Polygon((polar(m.DETENT_NOTCH_ROOT_R, angle_deg), polar(m.ROTOR_D / 2.0, angle_deg - half_angle), polar(m.ROTOR_D / 2.0, angle_deg + half_angle)))


def grip_capsule(angle_deg):
    straight = m.GRIP_TANGENTIAL_L - m.GRIP_RADIAL_W
    capsule = LineString(((-straight / 2.0, 0), (straight / 2.0, 0))).buffer(m.GRIP_RADIAL_W / 2.0, resolution=64)
    capsule = affinity.rotate(capsule, angle_deg + 90.0, origin=(0, 0))
    x, y = polar(m.GRIP_CENTER_R, angle_deg)
    return affinity.translate(capsule, x, y)


def main() -> None:
    m.validate_parameters()
    errors = []

    def require(condition, message):
        if not condition:
            errors.append(message)

    sector = rounded_annular_segment(m.SECTOR_R_IN, m.SECTOR_R_OUT, m.SECTOR_ANGLE_START_DEG, m.SECTOR_ANGLE_END_DEG, m.SECTOR_CORNER_R)
    raw_sector = raw_annular_segment(m.SECTOR_R_IN, m.SECTOR_R_OUT, m.SECTOR_ANGLE_START_DEG, m.SECTOR_ANGLE_END_DEG)
    portal = rounded_annular_segment(m.PORTAL_R_IN, m.PORTAL_R_OUT, m.PORTAL_ANGLE_START_DEG, m.PORTAL_ANGLE_END_DEG, m.PORTAL_CORNER_R)
    raw_portal = raw_annular_segment(m.PORTAL_R_IN, m.PORTAL_R_OUT, m.PORTAL_ANGLE_START_DEG, m.PORTAL_ANGLE_END_DEG)
    require(sector.difference(raw_sector).area <= EPS_AREA, "sector fillets escape sealed polar envelope")
    require(portal.difference(raw_portal).area <= EPS_AREA, "portal fillets escape sealed polar envelope")

    nominal_lens = lens(m.PETAL_L, m.PETAL_W)
    chamfer_lens = lens(m.PETAL_L + 2 * m.PETAL_ENTRY_CHAMFER, m.PETAL_W + 2 * m.PETAL_ENTRY_CHAMFER)
    nominal_petals = {bed: [place_radial(nominal_lens, xy) for xy in points] for bed, points in m.PETAL_BEDS.items()}
    chamfer_petals = [(bed, index, place_radial(chamfer_lens, xy)) for bed, points in m.PETAL_BEDS.items() for index, xy in enumerate(points)]

    state_rows = []
    ray_shift = (m.FRONT_SEAT_Z - (m.ROTOR_SEAT_Z + m.ROTOR_Z)) * math.tan(math.radians(20.0))
    for selected_bed, pose in m.ROTOR_STATES_DEG.items():
        world_sector = affinity.rotate(sector, pose, origin=(0, 0))
        selected_count = sum(petal.difference(world_sector).area <= EPS_AREA for petal in nominal_petals[selected_bed])
        nonselected_intersections = sum(
            petal.intersection(world_sector).area > EPS_AREA
            for bed, petals in nominal_petals.items() if bed != selected_bed
            for petal in petals
        )
        oblique_failures = 0
        for ray_angle in range(0, 360, 15):
            shifted_sector = affinity.translate(world_sector, ray_shift * math.cos(math.radians(ray_angle)), ray_shift * math.sin(math.radians(ray_angle)))
            oblique_failures += sum(petal.difference(shifted_sector).area > EPS_AREA for petal in nominal_petals[selected_bed])
            oblique_failures += sum(
                petal.intersection(shifted_sector).area > EPS_AREA
                for bed, petals in nominal_petals.items() if bed != selected_bed
                for petal in petals
            )
        require(selected_count == len(nominal_petals[selected_bed]), f"{selected_bed} selected count mismatch")
        require(nonselected_intersections == 0, f"{selected_bed} has nonselected optical intersection")
        require(oblique_failures == 0, f"{selected_bed} fails sampled +/-20 degree optical rays")
        state_rows.append({"bed": selected_bed, "pose_deg": pose, "selected_count": selected_count, "nonselected_intersections": nonselected_intersections, "oblique_ray_failures": oblique_failures})

    false_complete = []
    for pose in range(360):
        world_sector = affinity.rotate(sector, pose, origin=(0, 0))
        complete = [bed for bed, petals in nominal_petals.items() if all(petal.difference(world_sector).area <= EPS_AREA for petal in petals)]
        if len(complete) > 1:
            false_complete.append({"pose_deg": pose, "beds": complete})
    require(not false_complete, "full-turn sweep reveals multiple complete named beds")

    notch_rows = []
    for angle in m.DETENT_NOTCH_ANGLES_DEG:
        notch = notch_triangle(angle)
        distance = sector.distance(notch)
        notch_rows.append({"angle_deg": angle, "sector_distance_mm": round(distance, 6)})
        require(notch.difference(Point(0, 0).buffer(m.ROTOR_D / 2.0, resolution=1024)).area <= EPS_AREA, f"notch {angle} escapes rotor")
    minimum_notch_sector_distance = min(row["sector_distance_mm"] for row in notch_rows)
    require(minimum_notch_sector_distance >= m.REQUIRED_OUTER_WEB, "notch-to-sector web below 2.50 mm")
    require(abs(next(row["sector_distance_mm"] for row in notch_rows if row["angle_deg"] == 75.0) - 2.95) < 0.001, "+75 notch web is not 2.95 mm")

    grips = [grip_capsule(angle) for angle in m.GRIP_ANGLES_DEG]
    grip_trench = rounded_annular_segment(
        m.GRIP_CENTER_R - m.GRIP_RADIAL_W / 2.0,
        m.GRIP_CENTER_R + m.GRIP_RADIAL_W / 2.0,
        m.GRIP_TRENCH_ANGLE_START_DEG,
        m.GRIP_TRENCH_ANGLE_END_DEG,
        m.GRIP_TRENCH_CORNER_R,
    )
    grip_outside_home = sum(grip.difference(portal).area > EPS_AREA for grip in grips)
    nominal_grips_outside_trench = sum(grip.difference(grip_trench).area > EPS_AREA for grip in grips)
    trench_outside_portal_area = grip_trench.difference(portal).area
    other_pose_grip_hits = sum(
        affinity.rotate(grip, pose, origin=(0, 0)).intersection(portal).area > EPS_AREA
        for pose in (-120.0, -240.0)
        for grip in grips
    )
    other_pose_trench_hits = sum(
        affinity.rotate(grip_trench, pose, origin=(0, 0)).intersection(portal).area > EPS_AREA
        for pose in (-120.0, -240.0)
    )
    require(grip_outside_home == 0, "home grip patch escapes portal")
    require(nominal_grips_outside_trench == 0, "sealed grip footprint escapes printable trench")
    require(trench_outside_portal_area <= EPS_AREA, "printable grip trench escapes portal")
    require(other_pose_grip_hits == 0, "grip patch appears at another indexed pose")
    require(other_pose_trench_hits == 0, "printable grip trench appears at another indexed pose")
    bay_half_angle = math.degrees(math.asin((m.THUMB_BAY_Y / 2.0) / (m.GUIDE_ID / 2.0)))
    bay = raw_annular_segment(m.THUMB_BAY_X0, m.FRAME_X, -bay_half_angle, bay_half_angle)
    require(portal.difference(bay).area <= EPS_AREA, "front portal escapes rear bay")

    portal_leaks = 0
    for pose in range(360):
        portal_leaks += affinity.rotate(sector, pose, origin=(0, 0)).intersection(portal).area > EPS_AREA
        portal_leaks += any(affinity.rotate(notch_triangle(angle), pose, origin=(0, 0)).intersection(portal).area > EPS_AREA for angle in m.DETENT_NOTCH_ANGLES_DEG)
    require(portal_leaks == 0, "portal leaks sector or notch in full-turn sweep")

    minimum_chamfer_ligament = min(
        first[2].distance(second[2])
        for index, first in enumerate(chamfer_petals)
        for second in chamfer_petals[index + 1:]
    )
    require(minimum_chamfer_ligament >= 1.8, "rear chamfer ligament below 1.8 mm")

    stems = []
    for angle in m.REAR_STEM_ANGLES_DEG:
        stem = box(m.HUB_D / 2.0 - 0.2, -m.REAR_STEM_W / 2.0, m.FIELD_D / 2.0 + 2.0, m.REAR_STEM_W / 2.0)
        stem = affinity.rotate(stem, angle, origin=(0, 0))
        support = Point(*polar(m.THRUST_PAD_R, angle)).buffer(2.4, resolution=128)
        stems.append(stem.union(support))
    stem_hits = sum(petal.intersection(structure).area > EPS_AREA for petals in nominal_petals.values() for petal in petals for structure in stems)
    require(stem_hits == 0, "rear stem or thrust support occludes a petal")

    base = box(-m.FRAME_X / 2.0, -m.FRAME_Y / 2.0, m.FRAME_X / 2.0, m.FRAME_Y / 2.0).buffer(-m.FRAME_CORNER_R).buffer(m.FRAME_CORNER_R)
    base = base.difference(Point(0, 0).buffer(m.FIELD_D / 2.0, resolution=512)).difference(bay)
    underbeam = raw_annular_segment(m.FIELD_D / 2.0, m.DETENT_BEAM_R_OUT, m.DETENT_ROOT_ANGLE_DEG, m.DETENT_FREE_ANGLE_DEG)
    base = base.difference(underbeam)
    beam = raw_annular_segment(m.DETENT_BEAM_R_IN, m.DETENT_BEAM_R_OUT, m.DETENT_ROOT_ANGLE_DEG, m.DETENT_FREE_ANGLE_DEG)
    root_disk = Point(*polar(m.DETENT_CENTER_R, m.DETENT_ROOT_ANGLE_DEG)).buffer(m.DETENT_ROOT_FILLET_R, resolution=128)
    free_beam = beam.difference(root_disk.buffer(0.001))
    require(free_beam.intersection(base).area <= EPS_AREA, "detent free arc retains a base bridge")
    require(root_disk.intersection(base).area > 0.1, "detent root does not attach to base")

    source_text = (PROJECT / "moonwake_garden_lib.py").read_text()
    require("cadfits.slot_for(SPINDLE_D" in source_text and "cadfits.slot_for(ROTOR_D" in source_text, "mating diameters are not derived with cadfits")
    require(source_text.count("align=Z_MIN_ALIGN") >= 12, "axial primitives do not all declare bed datums")
    require("_detent_flexure" not in source_text, "rejected straight detent survived")

    result = {
        "schema_version": 1,
        "status": "pass" if not errors else "fail",
        "errors": errors,
        "radial_stack_mm": {
            "rotor_diameter": m.ROTOR_D,
            "guide_id": m.GUIDE_ID,
            "guide_od": m.GUIDE_OD,
            "normal_outer_web": m.ROTOR_NORMAL_OUTER_WEB,
            "minimum_notch_sector_distance": round(minimum_notch_sector_distance, 6),
            "required_outer_web": m.REQUIRED_OUTER_WEB,
            "tooth_to_notch_root_clearance": round(m.DETENT_TOOTH_TIP_R - m.DETENT_NOTCH_ROOT_R, 6),
        },
        "notches": notch_rows,
        "states": state_rows,
        "full_turn_multiple_complete_states": false_complete,
        "ray_shift_at_20_deg_mm": round(ray_shift, 6),
        "portal_full_turn_leaks": portal_leaks,
        "home_grips_outside_portal": grip_outside_home,
        "nominal_grips_outside_printable_trench": nominal_grips_outside_trench,
        "printable_trench_outside_portal_area_mm2": round(trench_outside_portal_area, 9),
        "other_pose_grip_hits": other_pose_grip_hits,
        "other_pose_printable_trench_hits": other_pose_trench_hits,
        "minimum_rear_chamfer_ligament_mm": round(minimum_chamfer_ligament, 6),
        "rear_stem_petal_intersections": stem_hits,
        "detent_free_arc_base_bridge_area_mm2": round(free_beam.intersection(base).area, 9),
        "detent_root_attachment_area_mm2": round(root_disk.intersection(base).area, 6),
        "evidence_limits": [
            "Planar geometry and B-rep gates do not prove elastic snap or detent force, fatigue, wear, or printer-process fit.",
            "Sampled oblique rays prove nominal geometric isolation at the checked angles, not observed brightness or human recognition.",
        ],
    }
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
