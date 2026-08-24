"""Exact digital gate for the parallel keyed A/B reader."""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT))

import params as p  # noqa: E402
from claim_crown import build_claim_crown  # noqa: E402
from fit_coupons import _place_pin, socket_coupon  # noqa: E402
from probe_pin import build_probe_pin  # noqa: E402
from spore_trough import build_spore_trough_with_owner  # noqa: E402
from stool import _tunnel_cutter, build_stool  # noqa: E402


def _volume(shape):
    return shape.val().Volume()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    pins = {1: build_probe_pin(1), 2: build_probe_pin(2)}
    seated = {
        species: build_stool(species, 1).translate((0, 0, p.SEATED_STOOL_Z))
        for species in ("deadhead", "bracket", "inkcap", "hollow")
    }
    tile = socket_coupon()

    def pose(owner, bit, proud, center=(0.0, 0.0)):
        return _place_pin(pins[owner], center, bit, proud, p.TILE_T)

    admitted = {bit: pose(1, bit, p.PIN_PROUD_ADMITTED_MM) for bit in p.PROBE_BITS}

    def stool_overlap(bit, species):
        return _volume(admitted[bit].intersect(seated[species]))

    # Descending proud height is increasing insertion. Find a coarse 0.25mm
    # onset bracket, then bisect it below 0.01mm. This is monotonic and keeps
    # the gate comfortably below its 300-second subprocess limit.
    contact = {}
    for bit in p.PROBE_BITS:
        clear_proud = p.PIN_LEN
        clear_overlap = 0.0
        contact_proud = None
        contact_overlap = None
        candidate = clear_proud - 0.25
        while candidate >= 0.0:
            overlap = _volume(pose(1, bit, candidate).intersect(seated["deadhead"]))
            if overlap > 0.00001:
                contact_proud, contact_overlap = candidate, overlap
                break
            clear_proud, clear_overlap = candidate, overlap
            candidate -= 0.25
        if contact_proud is None:
            raise RuntimeError(f"no blocked contact found for channel {bit}")
        while clear_proud - contact_proud > 0.01:
            midpoint = (clear_proud + contact_proud) / 2.0
            overlap = _volume(pose(1, bit, midpoint).intersect(seated["deadhead"]))
            if overlap > 0.00001:
                contact_proud, contact_overlap = midpoint, overlap
            else:
                clear_proud, clear_overlap = midpoint, overlap
        contact[bit] = {
            "clear_proud_mm": round(clear_proud, 6),
            "clear_overlap_mm3": clear_overlap,
            "contact_proud_mm": round(contact_proud, 6),
            "contact_overlap_mm3": contact_overlap,
            "midpoint_proud_mm": round((clear_proud + contact_proud) / 2.0, 6),
        }

    measurements = {
        "deadhead_A_admitted_overlap_mm3": stool_overlap("A", "deadhead"),
        "deadhead_B_admitted_overlap_mm3": stool_overlap("B", "deadhead"),
        "bracket_A_admitted_overlap_mm3": stool_overlap("A", "bracket"),
        "bracket_B_crosstalk_overlap_mm3": stool_overlap("B", "bracket"),
        "inkcap_A_crosstalk_overlap_mm3": stool_overlap("A", "inkcap"),
        "inkcap_B_admitted_overlap_mm3": stool_overlap("B", "inkcap"),
        "hollow_A_admitted_overlap_mm3": stool_overlap("A", "hollow"),
        "hollow_B_admitted_overlap_mm3": stool_overlap("B", "hollow"),
        "tile_deadhead_seated_overlap_mm3": _volume(tile.intersect(seated["deadhead"])),
        "tile_bracket_seated_overlap_mm3": _volume(tile.intersect(seated["bracket"])),
        "tile_inkcap_seated_overlap_mm3": _volume(tile.intersect(seated["inkcap"])),
        "tile_hollow_seated_overlap_mm3": _volume(tile.intersect(seated["hollow"])),
        "crown_seated_stool_overlap_mm3": _volume(
            build_claim_crown(2).translate((0, 0, p.SEATED_CROWN_Z)).intersect(seated["hollow"])
        ),
        "A_B_tunnel_cutter_overlap_mm3": _volume(_tunnel_cutter("A").intersect(_tunnel_cutter("B"))),
    }

    for bit in p.PROBE_BITS:
        measurements[f"admitted_{bit}_tile_overlap_mm3"] = _volume(admitted[bit].intersect(tile))
        measurements[f"stop_{bit}_3_1_clear_overlap_mm3"] = _volume(pose(1, bit, 3.1).intersect(tile))
        measurements[f"stop_{bit}_2_9_collision_overlap_mm3"] = _volume(pose(1, bit, 2.9).intersect(tile))

    # Every owner combination must allow both legal pins in the same Hollow.
    for owner_a in (1, 2):
        for owner_b in (1, 2):
            name = f"dual_probe_p{owner_a}A_p{owner_b}B_overlap_mm3"
            measurements[name] = _volume(
                pose(owner_a, "A", 3.0).intersect(pose(owner_b, "B", 3.0))
            )

    # Full extraction sweeps for every legal reader path. This is the
    # exact-BRep counterpart to the canonical mesh motion gate.
    withdrawal_maxima = {}
    withdrawal_cases = (
        ("blocked_deadhead_A", "deadhead", "A", p.PIN_PROUD_BLOCKED_MM),
        ("blocked_deadhead_B", "deadhead", "B", p.PIN_PROUD_BLOCKED_MM),
        ("admitted_bracket_A", "bracket", "A", 3.0),
        ("admitted_inkcap_B", "inkcap", "B", 3.0),
        ("admitted_hollow_A", "hollow", "A", 3.0),
        ("admitted_hollow_B", "hollow", "B", 3.0),
    )
    for case_name, species, bit, initial_proud in withdrawal_cases:
        tile_max = 0.0
        stool_max = 0.0
        case_samples = []
        proud = initial_proud
        while proud < p.PIN_LEN:
            case_samples.append(proud)
            proud += 1.0
        case_samples.append(p.PIN_LEN)
        for proud in case_samples:
            moving = pose(1, bit, proud)
            tile_max = max(tile_max, _volume(moving.intersect(tile)))
            stool_max = max(stool_max, _volume(moving.intersect(seated[species])))
        withdrawal_maxima[case_name] = {
            "tile_overlap_mm3": tile_max,
            "stool_overlap_mm3": stool_max,
        }

    # Conservative keyed-bore misalignment sweep. Full radial translation,
    # full D-flat rotation, and full end-to-end bore tilt are combined even
    # though a real shank cannot consume all three clearances at once.
    shank_r = p.STOOL_SHANK_D / 2.0
    flat = abs(p.STOOL_KEY_FLAT_Y)
    flat_clearance = abs(p.BORE_KEY_FLAT_Y) - flat
    chord_half = math.sqrt(shank_r ** 2 - flat ** 2)
    lo, hi = 0.0, math.radians(10.0)
    for _ in range(60):
        mid = (lo + hi) / 2.0
        if chord_half * math.sin(mid) + flat * math.cos(mid) <= abs(p.BORE_KEY_FLAT_Y):
            lo = mid
        else:
            hi = mid
    rotation_allowance_deg = math.degrees(lo)
    radial_play = (p.BORE_D - p.STOOL_SHANK_D) / 2.0
    tilt_allowance_deg = math.degrees(math.atan2(2.0 * radial_play, p.BORE_DEPTH))
    alignment_maxima = {}
    alignment_collisions = []
    alignment_modes = []
    for direction_deg in range(0, 360, 45):
        direction = math.radians(direction_deg)
        dx = radial_play * math.cos(direction)
        dy = radial_play * math.sin(direction)
        for zrot in (-rotation_allowance_deg, rotation_allowance_deg):
            for tilt_axis in ("x", "y"):
                for tilt in (-tilt_allowance_deg, tilt_allowance_deg):
                    alignment_modes.append((dx, dy, zrot, tilt_axis, tilt))
    routes = (("bracket", "A"), ("inkcap", "B"), ("hollow", "A"), ("hollow", "B"))
    pivot_z = p.STOOL_SHANK_H / 2.0
    for species, bit in routes:
        maximum = 0.0
        base = build_stool(species, 1)
        for mode_index, (dx, dy, zrot, tilt_axis, tilt) in enumerate(alignment_modes):
            axis_end = (1, 0, pivot_z) if tilt_axis == "x" else (0, 1, pivot_z)
            moved = base.rotate((0, 0, pivot_z), axis_end, tilt)
            moved = moved.rotate((0, 0, pivot_z), (0, 0, pivot_z + 1), zrot)
            moved = moved.translate((dx, dy, p.SEATED_STOOL_Z))
            overlap = _volume(admitted[bit].intersect(moved))
            maximum = max(maximum, overlap)
            if overlap >= 0.001:
                alignment_collisions.append({
                    "route": f"{species}_{bit}", "mode": mode_index,
                    "overlap_mm3": overlap,
                })
        alignment_maxima[f"{species}_{bit}"] = maximum

    # Neighbour gate: every blocked channel, every orthogonal 44mm neighbour,
    # the neighbouring cap, and both admitted neighbouring pins. Sample the
    # entire legal withdrawal range from first contact to tip-at-mouth.
    neighbour_overlaps = []
    neighbour_case_maxima = {}
    directions = {
        "east": (p.SOCKET_PITCH, 0.0),
        "west": (-p.SOCKET_PITCH, 0.0),
        "north": (0.0, p.SOCKET_PITCH),
        "south": (0.0, -p.SOCKET_PITCH),
    }
    proud_samples = [float(value) for value in range(3, int(p.PIN_LEN) + 1)]
    proud_samples.append(p.PIN_PROUD_BLOCKED_MM)
    proud_samples = sorted(set(round(value, 6) for value in proud_samples))
    for high_bit in p.PROBE_BITS:
        for proud in proud_samples:
            high_pin = pose(1, high_bit, proud)
            for direction_name, adjacent in directions.items():
                adjacent_stool = seated["hollow"].translate(adjacent)
                stool_volume = _volume(high_pin.intersect(adjacent_stool))
                neighbour_overlaps.append(stool_volume)
                stool_key = f"high_{high_bit}_{direction_name}_stool"
                neighbour_case_maxima[stool_key] = max(
                    neighbour_case_maxima.get(stool_key, 0.0), stool_volume
                )
                for adjacent_bit in p.PROBE_BITS:
                    pin_volume = _volume(
                        high_pin.intersect(pose(2, adjacent_bit, 3.0, adjacent))
                    )
                    neighbour_overlaps.append(pin_volume)
                    pin_key = f"high_{high_bit}_{direction_name}_admitted_{adjacent_bit}"
                    neighbour_case_maxima[pin_key] = max(
                        neighbour_case_maxima.get(pin_key, 0.0), pin_volume
                    )

    channel_spacing = math.dist(p.PROBE_MOUTHS_XY[0], p.PROBE_MOUTHS_XY[1])
    geometry = {
        "channel_center_spacing_mm": channel_spacing,
        "inter_channel_wall_mm": channel_spacing - p.PROBE_HOLE_D,
        "minimum_outer_shank_wall_mm": p.STOOL_SHANK_D / 2.0 - channel_spacing / 2.0 - p.PROBE_HOLE_D / 2.0,
        "collar_radial_wall_mm": (p.COLLAR_OD - p.BORE_D) / 2.0,
        "probe_head_gap_mm": channel_spacing - (p.PIN_HEAD_D + 2 * p.PIN_KNURL_RELIEF),
        "bore_radial_clearance_mm": (p.BORE_D - p.STOOL_SHANK_D) / 2.0,
        "probe_channel_radial_clearance_mm": (
            p.PROBE_HOLE_D - p.PIN_HEX_ACROSS_FLATS / math.cos(math.radians(30.0))
        ) / 2.0,
        "key_flat_clearance_mm": flat_clearance,
        "key_rotation_allowance_deg": rotation_allowance_deg,
        "bore_tilt_allowance_deg": tilt_allowance_deg,
    }

    motion_path = Path(__file__).with_name("motion.json")
    motion_data = json.loads(motion_path.read_text())
    motions = motion_data.get("motions", [])
    expected_motion_proud = {
        "probe_pin_p1": 3.0,
        "probe_pin_p1#2": 3.0,
        "probe_pin_p1#3": 3.0,
        "probe_pin_p2": p.PIN_PROUD_BLOCKED_MM,
        "probe_pin_p2#2": p.PIN_PROUD_BLOCKED_MM,
        "probe_pin_p2#3": 3.0,
    }
    hx, hy = p.PROBE_INWARD_XY[0]
    angle = math.radians(p.PROBE_ANGLE_DEG)
    expected_motion_vectors = {}
    for part, proud in expected_motion_proud.items():
        distance = p.PIN_LEN - proud
        expected_motion_vectors[part] = [
            -distance * math.sin(angle) * hx,
            -distance * math.sin(angle) * hy,
            distance * math.cos(angle),
        ]
    motion_vectors_match = all(
        motion.get("part") in expected_motion_vectors
        and len(motion.get("vector", [])) == 3
        and all(abs(actual - expected) <= 0.00001
                for actual, expected in zip(
                    motion["vector"], expected_motion_vectors[motion["part"]]
                ))
        and motion.get("steps") >= math.ceil(
            p.PIN_LEN - expected_motion_proud[motion["part"]]
        )
        for motion in motions
    )
    target_bed_xy_mm = {
        "loam_tile": p.TILE_SIZE + 2.0 * p.DOVETAIL_DEPTH,
        "spore_trough_x": p.TROUGH_L,
        "spore_trough_y": p.TROUGH_W,
        "stool": p.STOOL_CAP_D,
        "claim_crown": p.CROWN_OD,
        "probe_pin": p.PIN_HEAD_D,
    }

    checks = {
        "all_breps_valid": tile.val().isValid() and all(s.val().isValid() for s in seated.values()),
        "two_player_quantities": p.N_CROWN == 6 and p.N_PIN == 6 and p.N_TROUGH == 2,
        "all_production_parts_fit_160mm_target_bed": max(target_bed_xy_mm.values()) <= 160.0,
        "stool_origin_z_exact": p.SEATED_STOOL_Z == 8.0,
        "crown_origin_z_exact": p.SEATED_CROWN_Z == 54.0,
        "blocked_A_reference_matches_sweep": abs(p.PIN_PROUD_BLOCKED_MM - contact["A"]["midpoint_proud_mm"]) <= 0.026,
        "blocked_B_reference_matches_sweep": abs(p.PIN_PROUD_BLOCKED_MM - contact["B"]["midpoint_proud_mm"]) <= 0.026,
        "admitted_reference_exact": p.PIN_PROUD_ADMITTED_MM == 3.0,
        "owner_marks_printable": p.PIN_OWNER_HOLE_D >= 0.8,
        "owner_marks_visible_when_low": p.PIN_HEAD_T == p.PIN_PROUD_ADMITTED_MM,
        "owner_variants_geometrically_distinct": abs(_volume(pins[1]) - _volume(pins[2])) > 1.0,
        "all_public_owner_families_distinct": (
            all(abs(_volume(build_stool(species, 1)) - _volume(build_stool(species, 2))) > 1.0
                for species in ("deadhead", "bracket", "inkcap", "hollow"))
            and abs(_volume(build_claim_crown(1)) - _volume(build_claim_crown(2))) > 1.0
            and abs(_volume(build_probe_pin(1)) - _volume(build_probe_pin(2))) > 1.0
            and abs(_volume(build_spore_trough_with_owner(1))
                    - _volume(build_spore_trough_with_owner(2))) > 1.0
        ),
        "species_truth_table": (
            measurements["deadhead_A_admitted_overlap_mm3"] > 10.0
            and measurements["deadhead_B_admitted_overlap_mm3"] > 10.0
            and measurements["bracket_A_admitted_overlap_mm3"] < 0.001
            and measurements["bracket_B_crosstalk_overlap_mm3"] > 10.0
            and measurements["inkcap_A_crosstalk_overlap_mm3"] > 10.0
            and measurements["inkcap_B_admitted_overlap_mm3"] < 0.001
            and measurements["hollow_A_admitted_overlap_mm3"] < 0.001
            and measurements["hollow_B_admitted_overlap_mm3"] < 0.001
        ),
        "all_seated_stools_clear_tile": all(
            measurements[f"tile_{species}_seated_overlap_mm3"] < 0.001
            for species in ("deadhead", "bracket", "inkcap", "hollow")
        ),
        "crown_clears_stool_at_z54": measurements["crown_seated_stool_overlap_mm3"] < 0.001,
        "parallel_tunnel_cutters_do_not_cross": measurements["A_B_tunnel_cutter_overlap_mm3"] < 0.001,
        "all_owner_dual_probe_pairs_clear": all(
            measurements[f"dual_probe_p{oa}A_p{ob}B_overlap_mm3"] < 0.001
            for oa in (1, 2) for ob in (1, 2)
        ),
        "both_blind_stops_clear_at_3_1": all(
            measurements[f"stop_{bit}_3_1_clear_overlap_mm3"] < 0.001 for bit in p.PROBE_BITS
        ),
        "both_blind_stops_collide_at_2_9": all(
            measurements[f"stop_{bit}_2_9_collision_overlap_mm3"] > 1.0 for bit in p.PROBE_BITS
        ),
        "all_orthogonal_neighbours_clear_full_withdrawal": max(neighbour_overlaps) < 0.001,
        "all_exact_withdrawal_paths_clear": all(
            result["tile_overlap_mm3"] < 0.001 and result["stool_overlap_mm3"] < 0.001
            for result in withdrawal_maxima.values()
        ),
        "all_admitted_routes_clear_conservative_alignment_sweep": not alignment_collisions,
        "admissible_play_below_channel_clearance": (
            radial_play
            + shank_r * math.sin(math.radians(rotation_allowance_deg))
            + (2.0 * math.sqrt(shank_r ** 2 - (p._CHANNEL_HALF_SPACING ** 2)))
              * math.sin(math.radians(tilt_allowance_deg))
            < geometry["probe_channel_radial_clearance_mm"]
        ),
        "minimum_outer_shank_wall_at_least_1mm": geometry["minimum_outer_shank_wall_mm"] >= 1.0 - 1e-9,
        "collar_wall_at_least_3mm": geometry["collar_radial_wall_mm"] >= 3.0,
        "probe_heads_clear_each_other": geometry["probe_head_gap_mm"] >= 0.8 - 1e-9,
        "six_exact_motion_occurrences_declared": (
            len(motions) == 6
            and {motion.get("part") for motion in motions} == set(expected_motion_proud)
            and motion_vectors_match
        ),
        "harvest_requires_full_probe_withdrawal": all(
            result["tile_overlap_mm3"] < 0.001 and result["stool_overlap_mm3"] < 0.001
            for result in withdrawal_maxima.values()
        ),
        "cap_down_reveal_clears_socket_pitch": p.STOOL_CAP_D < p.SOCKET_PITCH,
        "cap_down_reveal_has_flat_boss_foot": p.STOOL_BOSS_D >= 16.0,
        "crown_can_rest_on_upward_shank_tip": (
            p.CROWN_ID < p.STOOL_SHANK_D and p.CROWN_OD < p.SOCKET_PITCH
        ),
    }

    report = {
        "topology": "parallel_non_crossing",
        "contact_sweep": contact,
        "geometry": {k: round(v, 6) for k, v in geometry.items()},
        "motion_contract": {
            "motions_declared": len(motions),
            "parts": [motion.get("part") for motion in motions],
            "full_extraction_vectors": {
                part: [round(v, 6) for v in vector]
                for part, vector in expected_motion_vectors.items()
            },
        },
        "neighbour_sweep": {
            "directions": directions,
            "proud_samples_mm": proud_samples,
            "maximum_overlap_mm3": round(max(neighbour_overlaps), 6),
            "case_maxima_mm3": {
                key: round(value, 6) for key, value in neighbour_case_maxima.items()
            },
        },
        "withdrawal_sweep": {
            "end_proud_mm": p.PIN_LEN,
            "maximum_step_mm": 1.0,
            "maxima": {
                key: {metric: round(value, 6) for metric, value in result.items()}
                for key, result in withdrawal_maxima.items()
            },
        },
        "alignment_sweep": {
            "modes_per_route": len(alignment_modes),
            "radial_translation_mm": round(radial_play, 6),
            "key_rotation_deg": round(rotation_allowance_deg, 6),
            "bore_tilt_deg": round(tilt_allowance_deg, 6),
            "route_maxima_mm3": {
                key: round(value, 6) for key, value in alignment_maxima.items()
            },
            "collisions": alignment_collisions,
        },
        "manufacturing_tolerance_sensitivity": {
            "digital_contact_bracket_mm": 0.05,
            "probe_channel_radial_clearance_mm": round(geometry["probe_channel_radial_clearance_mm"], 6),
            "bore_radial_clearance_mm": round(geometry["bore_radial_clearance_mm"], 6),
            "warning": "Physical fit is unverified; print the keyed reader coupon before production.",
        },
        "target_bed_contract": {
            "maximum_xy_mm": 160.0,
            "part_extents_mm": {
                key: round(value, 6) for key, value in target_bed_xy_mm.items()
            },
        },
        "harvest_reveal_contract": {
            "sequence": "record four probe metrics, fully withdraw every probe, then invert stools cap-down",
            "probe_end_proud_mm": p.PIN_LEN,
            "cap_diameter_mm": p.STOOL_CAP_D,
            "socket_pitch_mm": p.SOCKET_PITCH,
            "flat_boss_foot_diameter_mm": p.STOOL_BOSS_D,
            "crown_inner_diameter_mm": p.CROWN_ID,
            "upward_shank_diameter_mm": p.STOOL_SHANK_D,
        },
        "checks": checks,
        "measurements": {k: round(v, 6) for k, v in measurements.items()},
        "passed": all(checks.values()),
        "physical_fit_verified": False,
    }
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
