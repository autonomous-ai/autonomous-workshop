#!/usr/bin/env python3
"""Deterministic acoustic-geometry and datum audit for Rainspell Dial."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

import params as p  # noqa: E402
from features.primitives import polar_sector, rounded_radial_box  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def event_rows() -> list[dict]:
    rows = []
    fields = (
        ("rain", p.RAIN_ANGLES, p.RAIN_ARCS, p.RAIN_HEIGHTS),
        ("frog_song", p.FROG_ANGLES, p.FROG_ARCS, p.FROG_HEIGHTS),
        ("crickets", p.CRICKET_ANGLES, p.CRICKET_ARCS, p.CRICKET_HEIGHTS),
    )
    for field, angles, arcs, heights in fields:
        for index, (angle, arc, height) in enumerate(zip(angles, arcs, heights), start=1):
            packet = None
            radial_offset = 0.0
            if field == "frog_song":
                packet = (index - 1) // 3 + 1
            elif field == "crickets":
                packet = (index - 1) // 5 + 1
                radial_offset = p.CRICKET_PACKET_OFFSETS[packet - 1]
            rows.append(
                {
                    "field": field,
                    "ordinal": index,
                    "packet": packet,
                    "source_arc_mm": arc,
                    "source_angle_deg": angle,
                    "cad_transform_angle_deg": angle,
                    "angle_deviation_deg": 0.0,
                    "height_mm": height,
                    "root_width_mm": round(p.rib_root_width(height), 6),
                    "crest_width_mm": p.RIB_CREST_WIDTH,
                    "crest_radius_intent_mm": p.RIB_CREST_RADIUS,
                    "ramp_angle_intent_deg": p.RIB_RAMP_DEG,
                    "radial_offset_mm": radial_offset,
                }
            )
    return rows


def rounded_port_area(width: float) -> float:
    radius = p.PORT_FILLET_RADIUS
    return width * p.PORT_HEIGHT - (4.0 - math.pi) * radius * radius


def measured_port_area(width: float) -> float:
    sample_length = 2.0
    shape = rounded_radial_box(
        sample_length,
        width,
        p.PORT_HEIGHT,
        p.PORT_FILLET_RADIUS,
        10.0,
        0.0,
        0.0,
        round_ends=False,
    )
    return shape.volume / sample_length


def report() -> dict:
    circumference = 2.0 * math.pi * p.WORKING_RADIUS
    field_arc = circumference * p.FIELD_SPAN_DEG / 360.0
    transition_arc = circumference * p.PARTITION_GAP_DEG / 360.0
    chamber_rows = {}
    for key, target in p.CHAMBER_TARGETS.items():
        depth = p.CHAMBER_DEPTHS[key]
        brep_volume = polar_sector(
            p.CHAMBER_INNER_RADIUS,
            p.CHAMBER_OUTER_RADIUS,
            0.0,
            p.FIELD_SPAN_DEG,
            depth,
        ).volume
        chamber_rows[key] = {
            "target_volume_mm3": target,
            "modeled_sector_volume_mm3": round(brep_volume, 3),
            "difference_mm3": round(brep_volume - target, 3),
            "target_tolerance_mm3": p.CHAMBER_TOLERANCE,
            "depth_mm": round(depth, 6),
            "port_area_to_target_volume_per_mm": round(
                {"rain": 18.0, "frog_song": 15.0, "crickets": 24.0}[key] / target,
                7,
            ),
        }
    port_targets = {"rain": 18.0, "frog_song": 15.0, "crickets": 24.0}
    ports = {}
    for key, width in p.PORT_WIDTHS.items():
        ports[key] = {
            "rounded_bounding_width_mm": width,
            "height_mm": p.PORT_HEIGHT,
            "corner_radius_mm": p.PORT_FILLET_RADIUS,
            "target_area_mm2": port_targets[key],
            "formula_area_mm2": round(rounded_port_area(width), 4),
            "brep_section_area_mm2": round(measured_port_area(width), 4),
            "exit_angle_deg": p.PORT_EXIT_ANGLES[key],
            "centerplane_z_mm": p.PORT_CENTER_Z,
        }
    ports["rain"]["neck_centerline_length_mm"] = 4.0
    ports["frog_song"]["neck_centerline_length_mm"] = round(
        math.radians(p.FROG_NECK_END_DEG - p.FROG_NECK_START_DEG) * p.FROG_NECK_RADIUS,
        4,
    )
    ports["frog_song"]["neck_angle_range_deg"] = [p.FROG_NECK_START_DEG, p.FROG_NECK_END_DEG]
    ports["crickets"]["neck_centerline_length_mm"] = 3.0
    return {
        "schema_version": 1,
        "kind": "rainspell-dial.geometry-audit",
        "source_sha256": sha256(PROJECT / "params.py"),
        "assembly_step_sha256": sha256(PROJECT / "rainspell_dial.step"),
        "event_count": 46,
        "events": event_rows(),
        "cadence": {
            "working_circumference_mm": round(circumference, 4),
            "field_arc_mm": round(field_arc, 4),
            "transition_arc_mm": round(transition_arc, 4),
            "field_duration_s_at_10_15_rpm": [round(60.0 / 10.0 * p.FIELD_SPAN_DEG / 360.0, 4), round(60.0 / 15.0 * p.FIELD_SPAN_DEG / 360.0, 4)],
            "transition_duration_s_at_10_15_rpm": [round(60.0 / 10.0 * p.PARTITION_GAP_DEG / 360.0, 4), round(60.0 / 15.0 * p.PARTITION_GAP_DEG / 360.0, 4)],
            "sector_average_contacts_per_s_at_10_15_rpm": {
                "rain": [round(17 / (60.0 / 10.0 * p.FIELD_SPAN_DEG / 360.0), 2), round(17 / (60.0 / 15.0 * p.FIELD_SPAN_DEG / 360.0), 2)],
                "frog_song": [round(9 / (60.0 / 10.0 * p.FIELD_SPAN_DEG / 360.0), 2), round(9 / (60.0 / 15.0 * p.FIELD_SPAN_DEG / 360.0), 2)],
                "crickets": [round(20 / (60.0 / 10.0 * p.FIELD_SPAN_DEG / 360.0), 2), round(20 / (60.0 / 15.0 * p.FIELD_SPAN_DEG / 360.0), 2)],
            },
            "tangential_velocity_mm_s_at_10_15_rpm": [round(circumference * 10.0 / 60.0, 3), round(circumference * 15.0 / 60.0, 3)],
            "local_contacts_per_s": {
                "rain_pitch_4.0_to_5.2_mm": [7.85, 15.32],
                "frog_pitch_5.0_mm": [8.17, 12.25],
                "crickets_pitch_3.0_mm": [13.61, 20.42],
            },
            "claim_boundary": "Calculated contact cadence and rib-free travel only; not audible pitch, silence, timbre, loudness, or recognition.",
        },
        "chambers": chamber_rows,
        "ports": ports,
        "datums_and_clearances_mm": {
            "deck_top_z": p.DECK_TOP_Z,
            "cage_bottom_z": p.CAGE_BOTTOM_Z,
            "cage_to_tallest_rib": p.CAGE_BOTTOM_Z - (p.DECK_TOP_Z + max(p.FROG_HEIGHTS)),
            "wheel_skirt_to_guard_radial": p.GUARD_INNER_RADIUS - p.WHEEL_SKIRT_OUTER_RADIUS,
            "cage_to_guard_radial": p.GUARD_INNER_RADIUS - (p.FOLLOWER_CENTER_RADIUS + p.CAGE_RADIUS),
            "journal_diametral": 2.0 * (p.WHEEL_BORE_RADIUS - p.JOURNAL_RADIUS),
            "guide_diametral": 2.0 * (p.GUIDE_BORE_RADIUS - p.PLECTRUM_STEM_RADIUS),
            "wheel_endplay": p.WHEEL_ENDPLAY,
            "keeper_to_cap_swept": p.KEEPER_INNER_EDGE_RADIUS - p.CAP_SKIRT_RADII[1],
            "plectrum_head_top_valley_z": p.PLECTRUM_ASSEMBLY_Z + p.PLECTRUM_HEAD_TOP,
            "plectrum_head_top_max_rib_z": p.PLECTRUM_ASSEMBLY_Z + p.PLECTRUM_HEAD_TOP + max(p.FROG_HEIGHTS),
            "plectrum_head_top_design_travel_z": p.PLECTRUM_ASSEMBLY_Z + p.PLECTRUM_HEAD_TOP + p.FOLLOWER_TRAVEL,
        },
        "limitations": [
            "No exact physical print or slicer study has been performed.",
            "No microphone, loudness, pitch, or hearing-safety measurement has been performed.",
            "No human listening test establishes rain, frog-song, or cricket recognition or pleasantness.",
            "No gravity free-fall, inversion, shake, walking, tipping, bearing-noise, or retention test has been performed.",
            "No repeated-cycle wear or durability test has been performed.",
            "Dry labyrinth seams are serviceable and are not modeled or claimed as airtight Helmholtz resonators.",
            "Cricket-rib discrete striking versus boss bridging remains physically unverified.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", type=Path)
    args = parser.parse_args()
    value = report()
    data = json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    if args.write:
        args.write.write_text(data, encoding="utf-8")
        print(args.write)
    else:
        print(data, end="")
    targets = {"rain": 18.0, "frog_song": 15.0, "crickets": 24.0}
    for key, target in targets.items():
        assert abs(value["ports"][key]["brep_section_area_mm2"] - target) <= 0.01
        assert abs(value["chambers"][key]["difference_mm3"]) <= p.CHAMBER_TOLERANCE
    assert value["event_count"] == len(value["events"]) == 46
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
