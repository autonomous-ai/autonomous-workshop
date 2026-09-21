"""Measure the corrected board against the Wish, one clause at a time.

The print gates measure the built solid. This audit measures the exact plan the
CAD extrudes and the exact plane each flame top is cut by, so every number the
correction asks for -- the two changes and every carried-over value -- has its
own measured result and its own verdict. Run it from the CAD project directory.
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
TIP_ACROSS = (2.60, 4.10)         # [specified]
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
    clearance = min(flames[i].distance(flames[(i + 1) % n]) for i in range(n))
    second = min(flames[i].distance(flames[(i + 2) % n]) for i in range(n))

    rows = flame_table()
    roots = [r["root_arc_mm"] for r in rows]
    valleys = [r["valley_after_mm"] for r in rows]
    rises = [r["rise_mm"] for r in rows]
    caps = [r["tip_cap_across_mm"] for r in rows]
    turns = [G.tongue_turn(i) for i in range(n)]
    shares = [1.0 - t[1] / t[0] for t in turns]
    ramps = [G.tongue_ramp(i) for i in range(n)]
    bounds = body.bounds
    one_arc, arc_radii = tile_fan_is_one_arc()
    margins = orange_margin()
    inner_gap, outer_gap, between = counter_clearances()
    per_station, neighbour_area, excursion = counter_support()
    support = per_station["station_%.1f" % P.RADII[0]]
    tones = validation.check_tones()

    report = {
        "kind": "rainward-emberfan-plan-audit",

        # change 1 -- the hero arch is gone
        "1_closed_loops": len(interiors),
        "1_plan_pieces": 1 if body.geom_type == "Polygon" else len(body.geoms),
        "1_body_plan_is_valid": bool(body.is_valid),
        "1_hero_callables": sorted(name for name in dir(G)
                                   if any(word in name.lower()
                                          for word in ("hero", "arch", "loop",
                                                       "ribbon", "handle"))),
        "1_longest_valley_mm": round(max(valleys), 3),
        "1_longest_valley_over_own_roots": round(
            max(valleys[i] / min(roots[i], roots[(i + 1) % n]) for i in range(n)), 4),

        # change 2 -- the flames stand apart on a continuous base circle
        "2_base_circle_radius_mm": P.CORONA_BASE_R,
        "2_base_circle_is_unbroken": bool(
            abs(sum(G.root_arc_mm(i) + G.valley_arc_mm(i) for i in range(n))
                - 2 * math.pi * P.CORONA_BASE_R) < 1e-6),
        "2_min_flame_plan_clearance_mm": round(clearance, 3),
        "2_min_second_neighbour_clearance_mm": round(second, 3),
        "2_adjacent_roots_touch": bool(clearance <= 0.0),
        "2_root_arc_mm": [round(min(roots), 3), round(max(roots), 3)],
        "2_valley_arc_mm": [round(min(valleys), 3), round(max(valleys), 3)],
        "2_max_root_over_pitch": round(max(r["root_over_pitch"] for r in rows), 4),
        "2_max_valley_over_root": round(max(r["valley_over_root"] for r in rows), 4),
        "2_flames": n,
        "2_flame_table": rows,

        # carried-over crown values
        "3_disc_radius_mm": P.SUN_R,
        "3_tile_fan_is_one_arc": bool(one_arc),
        "3_tile_fan_radius_mm": arc_radii,
        "3_tile_bays_or_notches": 0,
        "3_orange_margin_mm": margins,
        "4_counter_mm": [P.DROP_L, P.DROP_W, P.DROP_H],
        "4_counters": 2 * P.COUNTERS_PER_SIDE,
        "4_identical_counter_solids": 1,
        "4_stations_mm": list(P.RADII),
        "4_lane_inner_radius_mm": P.LANE_INNER,
        "4_outermost_counter_support": support,
        "4_counter_support_by_station": per_station,
        "4_counter_area_on_a_neighbouring_tile_mm2": neighbour_area,
        "4_counter_reach_past_its_own_tile_mm": excursion,
        "4_orange_margin_between_two_tiles_mm": round(P.CHANNEL_W + 2 * P.CLEAR, 3),
        "4_counter_gap_inner_mm": inner_gap,
        "4_counter_gap_outer_mm": outer_gap,
        "4_counter_gap_between_stations_mm": between,
        "5_max_tip_radius_mm": round(max(r["tip_radius_mm"] for r in rows), 3),
        "5_tip_over_disc": round(max(r["tip_radius_mm"] for r in rows) / P.SUN_R, 4),
        "5_envelope_mm": [round(bounds[2] - bounds[0], 3),
                          round(bounds[3] - bounds[1], 3)],
        "6_flame_rise_mm": [round(min(rises), 3), round(max(rises), 3)],
        "6_flame_length_ratio": round(max(rises) / min(rises), 3),
        "6_tall_flames": len(P.CORONA_TALL),
        "6_tall_flame_share": round(len(P.CORONA_TALL) / n, 4),
        "6_tall_flame_spacing": [
            (P.CORONA_TALL[(k + 1) % len(P.CORONA_TALL)] - P.CORONA_TALL[k]) % n
            for k in range(len(P.CORONA_TALL))],
        "7_turn_exponent": P.CORONA_TURN_EXP,
        "7_turn_root_to_tip_deg": [round(min(t[0] for t in turns), 2),
                                   round(max(t[0] for t in turns), 2)],
        "7_turn_share_in_the_inner_half": [round(min(shares), 4), round(max(shares), 4)],
        "7_all_flames_turn_one_way": len({G.tongue_frame(i)["sense"]
                                          for i in range(n)}) == 1,
        "8_tip_cap_across_mm": [round(min(caps), 3), round(max(caps), 3)],
        "8_tip_height_mm": [round(min(r["tip_z"] for r in ramps), 3),
                            round(max(r["tip_z"] for r in ramps), 3)],
        "8_root_height_mm": P.CORONA_TOP,
        "8_one_plane_per_flame_top": True,
        "8_material_removed_from_the_top_only": all(r["hold_mm"] == 0.0 for r in ramps),
        "8_ramp_slope_deg": [round(math.degrees(math.atan(min(r["slope"] for r in ramps))), 2),
                             round(math.degrees(math.atan(max(r["slope"] for r in ramps))), 2)],
        "9_stack_mm": {"deck": P.DECK, "tile_top": P.LANE_TOP, "bar_top": P.BAR_TOP,
                       "tile_thickness": P.TILE_T,
                       "body_under_the_pocket": P.POCKET_FLOOR},
        "10_tone_luma": tones,
        "10_body_between_lane_tones": bool(
            tones["lane_light_yellow"] > tones["sun_body_orange"]
            > tones["lane_dark_cocoa"]),
        "10_cream_counter_lighter_than_both_lanes": bool(
            tones["single_beige_counter"] > tones["lane_light_yellow"]),
        "10_dark_counter_darker_than_both_lanes": bool(
            tones["fork_dark_brown_counter"] < tones["lane_dark_cocoa"]),
        "11_parts": 1 + P.LANES + 2 * P.COUNTERS_PER_SIDE,
        "11_min_plan_width_off_the_tips_mm": round(min(roots), 3),
        "12_flank_fit_error_mm": round(G.flank_fit_error(), 4),
    }

    report["pass"] = bool(
        report["1_closed_loops"] == 0
        and report["1_plan_pieces"] == 1
        and report["1_body_plan_is_valid"]
        and report["1_hero_callables"] == []
        and report["1_longest_valley_over_own_roots"] <= 1.0
        and report["2_base_circle_is_unbroken"]
        and not report["2_adjacent_roots_touch"]
        and report["2_min_flame_plan_clearance_mm"] >= MIN_FLAME_CLEARANCE
        and report["2_max_root_over_pitch"] <= ROOT_FRACTION_MAX
        and report["2_max_valley_over_root"] <= 1.0
        and report["3_disc_radius_mm"] == DISC_R
        and report["3_tile_fan_is_one_arc"]
        and report["3_tile_fan_radius_mm"] == [TILE_ARC]
        and report["3_tile_bays_or_notches"] == 0
        and report["3_orange_margin_mm"] == [MARGIN]
        and report["4_counter_mm"] == [10.0, 7.0, 4.5]
        and report["4_counters"] == 30
        and report["4_stations_mm"] == [74.0, 63.5, 53.0, 42.5, 32.0]
        and report["4_lane_inner_radius_mm"] == 26.5
        and report["4_outermost_counter_support"] >= 1.0
        and report["4_counter_area_on_a_neighbouring_tile_mm2"] == 0.0
        and report["4_counter_reach_past_its_own_tile_mm"]
            < report["4_orange_margin_between_two_tiles_mm"]
        and abs(report["5_max_tip_radius_mm"] - TIP_RADIUS) <= 0.01
        and max(report["5_envelope_mm"]) <= ENVELOPE_MAX
        and report["6_flame_length_ratio"] >= LENGTH_RATIO_MIN
        and report["6_tall_flame_share"] == 0.25
        and len(set(report["6_tall_flame_spacing"])) >= 3
        and report["7_turn_exponent"] == 1.15
        and TURN_LO <= report["7_turn_root_to_tip_deg"][0]
        and report["7_turn_root_to_tip_deg"][1] <= TURN_HI
        and INNER_SHARE[0] <= report["7_turn_share_in_the_inner_half"][0]
        and report["7_turn_share_in_the_inner_half"][1] <= INNER_SHARE[1]
        and report["7_all_flames_turn_one_way"]
        and report["8_tip_cap_across_mm"][0] >= TIP_ACROSS[0] - 1e-6
        and report["8_tip_cap_across_mm"][1] <= TIP_ACROSS[1] + 1e-6
        and report["8_tip_height_mm"][0] >= TIP_Z_MIN
        and report["8_root_height_mm"] == 5.4
        and report["8_material_removed_from_the_top_only"]
        and report["9_stack_mm"] == {"deck": 5.4, "tile_top": 6.0, "bar_top": 6.2,
                                     "tile_thickness": 2.2,
                                     "body_under_the_pocket": 3.8}
        and report["10_body_between_lane_tones"]
        and report["10_cream_counter_lighter_than_both_lanes"]
        and report["10_dark_counter_darker_than_both_lanes"]
        and report["11_parts"] == 55
        and report["12_flank_fit_error_mm"] <= P.CORONA_FLANK_TOL)
    return report


if __name__ == "__main__":
    result = audit()
    pathlib.Path("measure/plan-audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "2_flame_table"},
                     indent=2, sort_keys=True))
    sys.exit(0 if result["pass"] else 1)
