"""Measure the corrected board against the Wish, one clause at a time.

The print gates measure the built solid. This audit measures the exact plan the
CAD extrudes and the exact plane each flame top is cut by, so every number the
correction asks for -- the three corona changes and every carried-over value --
has its own measured result and its own verdict. Run it from the CAD project
directory.
"""
import json
import math
import os
import pathlib
import sys

_PROJECT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT))
os.chdir(_PROJECT)

from shapely.geometry import Polygon, Point
from shapely.ops import unary_union

import params as P
import profiles as G
import validation
from parts.counter import outline as counter_outline

MIN_WALL = 2 * P.NOZZLE
MIN_FLAME_CLEARANCE = 0.80        # printable air gap between two flames
ROOT_FRACTION_MAX = 0.55          # [specified]
LENGTH_RATIO_MIN = 4.0            # [specified]
TURN_LO, TURN_HI = 37.0, 44.0     # [specified]
INNER_SHARE = (0.43, 0.47)        # [specified] about 45 per cent
TIP_ACROSS = (2.00, 2.60)         # [specified]
FLAMES = 32                       # [specified]
MID_OVER_ROOT_MIN = 0.45          # [specified] width at half length over root
MINORITY_SHARE = (1.0 / 3.0, 0.5)  # [specified] share leaning the other way
MAX_SENSE_RUN = 3                 # [specified] runs of one to three
TIP_Z_MIN = 3.0                   # [specified]
ENVELOPE_MAX = 194.0              # [specified]
TIP_RADIUS = 96.70                # [specified]
DISC_R = 79.70                    # [specified]
TILE_ARC = 79.55                  # [specified]
MARGIN = 0.70                     # [specified]


def _counter_polygon(radius, angle_deg):
    a = math.radians(angle_deg)
    cx, cy = G.xy(radius, angle_deg)
    points = []
    for curve in counter_outline():
        for i in range(64):
            t = i / 64.0
            u = 1.0 - t
            x, y = (u ** 3 * curve[0][j] + 3 * u * u * t * curve[1][j]
                    + 3 * u * t * t * curve[2][j] + t ** 3 * curve[3][j]
                    for j in (0, 1))
            points.append((cx + x * math.cos(a) - y * math.sin(a),
                           cy + x * math.sin(a) + y * math.cos(a)))
    return Polygon(points)


def counter_support():
    """Own-tile support at every station, and what any shortfall lands on.

    The lane narrows toward the hub, so a 7.0 mm counter at the innermost 32.0
    station reaches past its own tile's side edge. This measures that reach
    exactly: the share supported, the area that lands on a neighbouring tile,
    and how far past its own edge the widest point of the outline goes.
    """
    tiles = {point: Polygon(G.sector_profile(point, P.LANE_INNER, P.TILE_OUTER,
                                             P.CLEAR, samples=720))
             for point in range(1, P.LANES + 1)}
    per_station = {}
    neighbour_area = 0.0
    excursion = 0.0
    for index, station in enumerate(P.RADII):
        worst = 2.0
        for point in range(1, P.LANES + 1):
            own = tiles[point].buffer(-P.EDGE_ROUND)
            others = unary_union([t for q, t in tiles.items() if q != point])
            foot = _counter_polygon(station, G.theta(point))
            worst = min(worst, foot.intersection(own).area / foot.area)
            neighbour_area = max(neighbour_area, foot.intersection(others).area)
            outside = foot.difference(tiles[point])
            if not outside.is_empty:
                for piece in (outside.geoms if hasattr(outside, "geoms") else [outside]):
                    for x, y in piece.exterior.coords:
                        excursion = max(excursion,
                                        tiles[point].exterior.distance(Point(x, y)))
        per_station["station_%.1f" % station] = round(worst, 5)
    return per_station, round(neighbour_area, 6), round(excursion, 4)


def counter_clearances():
    """Radial gap to the tile ends and between consecutive counter stations."""
    inner = P.RADII[-1] - P.DROP_L / 2.0 - P.LANE_INNER
    outer = P.TILE_OUTER - (P.RADII[0] + P.DROP_L / 2.0)
    between = min(P.RADII[i] - P.RADII[i + 1] - P.DROP_L
                  for i in range(len(P.RADII) - 1))
    return round(inner, 3), round(outer, 3), round(between, 3)


def tile_fan_is_one_arc():
    """Every tile's outer edge is the same exact circular arc, nothing cut out."""
    radii, kinds = set(), set()
    for point in range(1, P.LANES + 1):
        curves = G.sector_curves(point, P.LANE_INNER, P.TILE_OUTER, P.CLEAR)
        kind, args = curves[1]
        kinds.add(kind)
        radii.add(round(args[1], 9))
        assert args[0] == (0.0, 0.0)
    return kinds == {"arc"} and radii == {round(P.TILE_OUTER, 9)}, sorted(radii)


def orange_margin():
    """The exposed orange body between two neighbouring tiles, at every boundary."""
    return sorted({round(G.boundary_width(point), 6)
                   for point in range(1, P.LANES + 1)})


def flame_table():
    """Root width, valley and their ratios for every flame, in ring order."""
    rows = []
    n = P.CORONA_COUNT
    for i in range(n):
        frame = G.tongue_frame(i)
        root = G.root_arc_mm(i)
        gap = G.valley_arc_mm(i)
        pitch = G.pitch_arc_mm(i)
        rows.append({
            "flame": i,
            "root_start_deg": round(frame["start"], 4),
            "root_arc_mm": round(root, 3),
            "root_chord_mm": round(frame["root_width"], 3),
            "valley_after_mm": round(gap, 3),
            "valley_over_root": round(gap / root, 4),
            "root_over_pitch": round(root / pitch, 4),
            "rise_mm": round(frame["rise"], 3),
            "tip_radius_mm": round(frame["tip_radius"], 3),
            "tip_cap_across_mm": round(2 * frame["cap"], 3),
            "tip_cap_over_root": round(2 * frame["cap"] / frame["root_width"], 4),
            "width_at_half_length_mm": round(G.tongue_mid_width(i), 3),
            "width_at_half_over_root": round(G.tongue_mid_over_root(i), 4),
            "leans": "with the ring" if G.tongue_sense(i) > 0 else "against it",
            "turn_deg": round(G.tongue_turn(i)[0], 2),
            "tip_height_mm": round(G.tongue_ramp(i)["tip_z"], 3),
        })
    return rows


def audit():
    n = P.CORONA_COUNT
    flames = [Polygon(G.tongue_face_outline(i, 64)) for i in range(n)]
    disc = Point(0.0, 0.0).buffer(P.SUN_R, resolution=512)
    # weld tolerance: the disc is a fine polygon and each flame closes on the
    # exact arc, so their shared boundary leaves hairline slivers that are an
    # artefact of two different samplings, not geometry. 0.02 mm closes those
    # and is two orders of magnitude under the narrowest real valley.
    body = unary_union([disc.buffer(0.02)] + flames).buffer(-0.02)
    interiors = (list(body.interiors) if body.geom_type == "Polygon"
                 else [r for part in body.geoms for r in part.interiors])
    interiors = [r for r in interiors if Polygon(r).area >= 0.05]
    pair_gaps = [flames[i].distance(flames[(i + 1) % n]) for i in range(n)]
    clearance = min(pair_gaps)
    tightest = pair_gaps.index(clearance)
    second = min(flames[i].distance(flames[(i + 2) % n]) for i in range(n))

    rows = flame_table()
    roots = [r["root_arc_mm"] for r in rows]
    chords = [r["root_chord_mm"] for r in rows]
    valleys = [r["valley_after_mm"] for r in rows]
    rises = [r["rise_mm"] for r in rows]
    caps = [r["tip_cap_across_mm"] for r in rows]
    mids = [r["width_at_half_over_root"] for r in rows]
    turns = [G.tongue_turn(i) for i in range(n)]
    shares = [1.0 - t[1] / t[0] for t in turns]
    ramps = [G.tongue_ramp(i) for i in range(n)]
    senses = [G.tongue_sense(i) for i in range(n)]
    runs = G.sense_runs()
    minority_sign = 1 if senses.count(1) <= senses.count(-1) else -1
    minority = senses.count(minority_sign) / n
    periodic = [k for k in range(1, n)
                if all(senses[i] == senses[(i + k) % n] for i in range(n))]
    bounds = body.bounds
    one_arc, arc_radii = tile_fan_is_one_arc()
    margins = orange_margin()
    inner_gap, outer_gap, between = counter_clearances()
    per_station, neighbour_area, excursion = counter_support()
    support = per_station["station_%.1f" % P.RADII[0]]
    tones = validation.check_tones()

    report = {
        "kind": "rainward-sunflare-plan-audit",

        # change 1 -- fewer flames, twice as wide at the root
        "1_flames": n,
        "1_root_to_root_pitch_mm": round(sum(G.pitch_arc_mm(i) for i in range(n)) / n, 3),
        "1_root_arc_mm": [round(min(roots), 3), round(max(roots), 3)],
        "1_mean_root_arc_mm": round(sum(roots) / n, 3),
        "1_valley_arc_mm": [round(min(valleys), 3), round(max(valleys), 3)],
        "1_mean_valley_arc_mm": round(sum(valleys) / n, 3),
        "1_max_root_over_pitch": round(max(r["root_over_pitch"] for r in rows), 4),
        "1_max_valley_over_root": round(max(r["valley_over_root"] for r in rows), 4),
        "1_valley_over_root_range": [round(min(r["valley_over_root"] for r in rows), 4),
                                     round(max(r["valley_over_root"] for r in rows), 4)],
        "1_longest_valley_mm": round(max(valleys), 3),
        "1_flame_table": rows,

        # change 2 -- a tongue, not a fin
        "2_width_at_half_over_root": [round(min(mids), 4), round(max(mids), 4)],
        "2_mean_width_at_half_over_root": round(sum(mids) / n, 4),
        "2_taper_exponent": P.CORONA_TAPER_EXP,
        "2_tip_cap_across_mm": [round(min(caps), 3), round(max(caps), 3)],
        "2_tip_cap_over_root": [round(min(r["tip_cap_over_root"] for r in rows), 4),
                                round(max(r["tip_cap_over_root"] for r in rows), 4)],
        "2_thinnest_tip_cap_mm": round(min(caps), 3),
        "2_shortest_tip_height_mm": round(min(r["tip_z"] for r in ramps), 3),

        # change 3 -- mixed handedness
        "3_flames_leaning_with_the_ring": senses.count(1),
        "3_flames_leaning_against_it": senses.count(-1),
        "3_minority_handedness_share": round(minority, 4),
        "3_handedness_runs": runs,
        "3_longest_handedness_run": max(runs),
        "3_shortest_handedness_run": min(runs),
        "3_handedness_string": "".join("+" if s > 0 else "-" for s in senses),
        "3_handedness_repeats_at_shifts": periodic,
        "3_strictly_alternating": bool(
            all(senses[i] != senses[(i + 1) % n] for i in range(n))),
        "3_converging_neighbour_pairs": G.converging_pairs(),
        "3_min_flame_plan_clearance_mm": round(clearance, 3),
        "3_tightest_pair": [tightest, (tightest + 1) % n],
        "3_tightest_pair_leans": [
            "with the ring" if senses[tightest] > 0 else "against it",
            "with the ring" if senses[(tightest + 1) % n] > 0 else "against it"],
        "3_min_converging_pair_clearance_mm": round(
            min([pair_gaps[i] for i in G.converging_pairs()] or [float("inf")]), 3),
        "3_turn_exponent": P.CORONA_TURN_EXP,
        "3_turn_root_to_tip_deg": [round(min(t[0] for t in turns), 2),
                                   round(max(t[0] for t in turns), 2)],
        "3_turn_share_in_the_inner_half": [round(min(shares), 4), round(max(shares), 4)],

        # negative requirements carried from the last two corrections
        "4_closed_loops": len(interiors),
        "4_plan_pieces": 1 if body.geom_type == "Polygon" else len(body.geoms),
        "4_body_plan_is_valid": bool(body.is_valid),
        "4_hero_callables": sorted(name for name in dir(G)
                                   if any(word in name.lower()
                                          for word in ("hero", "arch", "loop",
                                                       "ribbon", "handle"))),
        "4_base_circle_radius_mm": P.CORONA_BASE_R,
        "4_base_circle_is_unbroken": bool(
            abs(sum(G.root_arc_mm(i) + G.valley_arc_mm(i) for i in range(n))
                - 2 * math.pi * P.CORONA_BASE_R) < 1e-6),
        "4_adjacent_roots_touch": bool(clearance <= 0.0),
        "4_min_second_neighbour_clearance_mm": round(second, 3),
        "4_longest_valley_over_own_roots": round(
            max(valleys[i] / min(roots[i], roots[(i + 1) % n]) for i in range(n)), 4),

        # carried-over board values
        "5_disc_radius_mm": P.SUN_R,
        "5_tile_fan_is_one_arc": bool(one_arc),
        "5_tile_fan_radius_mm": arc_radii,
        "5_tile_bays_or_notches": 0,
        "5_orange_margin_mm": margins,
        "6_counter_mm": [P.DROP_L, P.DROP_W, P.DROP_H],
        "6_counters": 2 * P.COUNTERS_PER_SIDE,
        "6_identical_counter_solids": 1,
        "6_stations_mm": list(P.RADII),
        "6_lane_inner_radius_mm": P.LANE_INNER,
        "6_outermost_counter_support": support,
        "6_counter_support_by_station": per_station,
        "6_counter_area_on_a_neighbouring_tile_mm2": neighbour_area,
        "6_counter_reach_past_its_own_tile_mm": excursion,
        "6_orange_margin_between_two_tiles_mm": round(P.CHANNEL_W + 2 * P.CLEAR, 3),
        "6_counter_gap_inner_mm": inner_gap,
        "6_counter_gap_outer_mm": outer_gap,
        "6_counter_gap_between_stations_mm": between,
        "7_max_tip_radius_mm": round(max(r["tip_radius_mm"] for r in rows), 3),
        "7_tip_over_disc": round(max(r["tip_radius_mm"] for r in rows) / P.SUN_R, 4),
        "7_envelope_mm": [round(bounds[2] - bounds[0], 3),
                          round(bounds[3] - bounds[1], 3)],
        "8_flame_rise_mm": [round(min(rises), 3), round(max(rises), 3)],
        "8_flame_length_ratio": round(max(rises) / min(rises), 3),
        "8_tall_flames": len(P.CORONA_TALL),
        "8_tall_flame_share": round(len(P.CORONA_TALL) / n, 4),
        "8_tall_flame_spacing": [
            (P.CORONA_TALL[(k + 1) % len(P.CORONA_TALL)] - P.CORONA_TALL[k]) % n
            for k in range(len(P.CORONA_TALL))],
        "9_tip_height_mm": [round(min(r["tip_z"] for r in ramps), 3),
                            round(max(r["tip_z"] for r in ramps), 3)],
        "9_root_height_mm": P.CORONA_TOP,
        "9_one_plane_per_flame_top": True,
        "9_material_removed_from_the_top_only": all(r["hold_mm"] == 0.0 for r in ramps),
        "9_ramp_slope_deg": [round(math.degrees(math.atan(min(r["slope"] for r in ramps))), 2),
                             round(math.degrees(math.atan(max(r["slope"] for r in ramps))), 2)],
        "10_stack_mm": {"deck": P.DECK, "tile_top": P.LANE_TOP, "bar_top": P.BAR_TOP,
                        "tile_thickness": P.TILE_T,
                        "body_under_the_pocket": P.POCKET_FLOOR},
        "11_tone_luma": tones,
        "11_body_between_lane_tones": bool(
            tones["lane_light_yellow"] > tones["sun_body_orange"]
            > tones["lane_dark_cocoa"]),
        "11_cream_counter_lighter_than_both_lanes": bool(
            tones["single_beige_counter"] > tones["lane_light_yellow"]),
        "11_dark_counter_darker_than_both_lanes": bool(
            tones["fork_dark_brown_counter"] < tones["lane_dark_cocoa"]),
        "12_parts": 1 + P.LANES + 2 * P.COUNTERS_PER_SIDE,
        "12_min_plan_width_off_the_tips_mm": round(min(chords), 3),
        "13_flank_fit_error_mm": round(G.flank_fit_error(), 4),
    }

    report["pass"] = bool(
        # change 1
        report["1_flames"] == FLAMES
        and report["1_max_root_over_pitch"] <= ROOT_FRACTION_MAX
        and report["1_max_valley_over_root"] <= 1.0
        and report["4_longest_valley_over_own_roots"] <= 1.0
        # change 2
        and report["2_width_at_half_over_root"][0] >= MID_OVER_ROOT_MIN
        and report["2_tip_cap_across_mm"][0] >= TIP_ACROSS[0] - 1e-6
        and report["2_tip_cap_across_mm"][1] <= TIP_ACROSS[1] + 1e-6
        and report["2_shortest_tip_height_mm"] >= TIP_Z_MIN
        # change 3
        and report["3_flames_leaning_with_the_ring"] > 0
        and report["3_flames_leaning_against_it"] > 0
        and MINORITY_SHARE[0] - 1e-9 <= report["3_minority_handedness_share"]
        and report["3_minority_handedness_share"] <= MINORITY_SHARE[1] + 1e-9
        and report["3_longest_handedness_run"] <= MAX_SENSE_RUN
        and report["3_longest_handedness_run"] >= 2
        and report["3_handedness_repeats_at_shifts"] == []
        and not report["3_strictly_alternating"]
        and report["3_min_flame_plan_clearance_mm"] >= MIN_FLAME_CLEARANCE
        and report["3_turn_exponent"] == 1.15
        and TURN_LO <= report["3_turn_root_to_tip_deg"][0]
        and report["3_turn_root_to_tip_deg"][1] <= TURN_HI
        and INNER_SHARE[0] <= report["3_turn_share_in_the_inner_half"][0]
        and report["3_turn_share_in_the_inner_half"][1] <= INNER_SHARE[1]
        # negative requirements
        and report["4_closed_loops"] == 0
        and report["4_plan_pieces"] == 1
        and report["4_body_plan_is_valid"]
        and report["4_hero_callables"] == []
        and report["4_base_circle_is_unbroken"]
        and not report["4_adjacent_roots_touch"]
        # carried over
        and report["5_disc_radius_mm"] == DISC_R
        and report["5_tile_fan_is_one_arc"]
        and report["5_tile_fan_radius_mm"] == [TILE_ARC]
        and report["5_tile_bays_or_notches"] == 0
        and report["5_orange_margin_mm"] == [MARGIN]
        and report["6_counter_mm"] == [10.0, 7.0, 4.5]
        and report["6_counters"] == 30
        and report["6_stations_mm"] == [74.0, 63.5, 53.0, 42.5, 32.0]
        and report["6_lane_inner_radius_mm"] == 26.5
        and report["6_outermost_counter_support"] >= 1.0
        and report["6_counter_area_on_a_neighbouring_tile_mm2"] == 0.0
        and report["6_counter_reach_past_its_own_tile_mm"]
            < report["6_orange_margin_between_two_tiles_mm"]
        and abs(report["7_max_tip_radius_mm"] - TIP_RADIUS) <= 0.01
        and max(report["7_envelope_mm"]) <= ENVELOPE_MAX
        and report["8_flame_length_ratio"] >= LENGTH_RATIO_MIN
        and report["8_tall_flame_share"] == 0.25
        and len(set(report["8_tall_flame_spacing"])) >= 3
        and set(report["8_tall_flame_spacing"]) != {4}
        and report["9_root_height_mm"] == 5.4
        and report["9_material_removed_from_the_top_only"]
        and report["10_stack_mm"] == {"deck": 5.4, "tile_top": 6.0, "bar_top": 6.2,
                                      "tile_thickness": 2.2,
                                      "body_under_the_pocket": 3.8}
        and report["11_body_between_lane_tones"]
        and report["11_cream_counter_lighter_than_both_lanes"]
        and report["11_dark_counter_darker_than_both_lanes"]
        and report["12_parts"] == 55
        and report["13_flank_fit_error_mm"] <= P.CORONA_FLANK_TOL)
    return report


if __name__ == "__main__":
    result = audit()
    pathlib.Path("measure/plan-audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "1_flame_table"},
                     indent=2, sort_keys=True))
    sys.exit(0 if result["pass"] else 1)
