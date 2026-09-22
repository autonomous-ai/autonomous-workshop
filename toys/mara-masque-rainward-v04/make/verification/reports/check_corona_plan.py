"""Measure the corona skirt against the correction Wish, one clause at a time.

The thickness gate measures the built solid. This audit measures the exact plan
the CAD extrudes, so every number the correction asks for -- tongue count,
unbroken perimeter, root width, length variation, flame depth, nothing
floating, one hero loop -- has its own measured value and its own verdict.
Run it from the CAD project directory.
"""
import json
import os
import pathlib
import sys
from math import atan2, degrees, hypot

_PROJECT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT))
os.chdir(_PROJECT)

from math import cos, radians, sin

from shapely.geometry import Polygon
from shapely.ops import unary_union

import params as P
import profiles as G
from parts.counter import FORK_CURVES, SINGLE_CURVES

MIN_WALL = 2 * P.NOZZLE
FRINGE = 0.64             # the plan width below which the wall gate complains;
                          # the lane boundaries draft wider below the surface
PLAIN_BAND = 0.5          # mm either side of radius 90 that still counts as plain
PLAIN_LIMIT = 4.0         # deg of plain circular edge the Wish allows
MIN_TONGUES, MAX_TONGUES = 32, 44
MIN_ROOT_MM = 6.0
MIN_ROOT_SHARE = 0.60
MIN_LENGTH_RATIO = 2.0
DEEP_MM = 9.0
MIN_DEEP_TROUGHS = 5
def _counter_outline(curves):
    points = []
    for curve in curves:
        for i in range(96):
            t = i / 96.0
            u = 1.0 - t
            points.append(tuple(
                u ** 3 * curve[0][j] + 3 * u * u * t * curve[1][j]
                + 3 * u * t * t * curve[2][j] + t ** 3 * curve[3][j] for j in (0, 1)))
    return points


OUTLINES = {"single": _counter_outline(SINGLE_CURVES),
            "fork": _counter_outline(FORK_CURVES)}


def _placed(kind, radius, angle_deg):
    a = radians(angle_deg)
    cx, cy = G.xy(radius, angle_deg)
    return Polygon([(cx + x * cos(a) - y * sin(a), cy + x * sin(a) + y * cos(a))
                    for x, y in OUTLINES[kind]])


def outer_counter_support(clipped):
    """Worst share of an outermost counter that lands on its own tile top."""
    worst = 2.0
    for point in range(1, P.LANES + 1):
        top = Polygon(G.sector_profile(point, P.LANE_INNER, P.TILE_OUTER, P.CLEAR,
                                       clipped=clipped)).buffer(-P.EDGE_ROUND)
        for kind in ("single", "fork"):
            foot = _placed(kind, P.RADII[0], G.theta(point))
            worst = min(worst, foot.intersection(top).area / foot.area)
    return worst


def _ring_polar(polygon):
    polar, base = [], None
    for x, y in list(polygon.exterior.coords)[:-1]:
        a = degrees(atan2(y, x))
        if base is not None:
            while a - base > 180.0:
                a -= 360.0
            while a - base < -180.0:
                a += 360.0
        base = a
        polar.append((a, hypot(x, y)))
    if polar[-1][0] < polar[0][0]:
        polar.reverse()
    return polar


def _longest_plain_run(polar):
    doubled = polar + [(a + 360.0, r) for a, r in polar]
    worst, start = 0.0, None
    for a, r in doubled:
        if abs(r - P.SUN_R) <= PLAIN_BAND:
            start = a if start is None else start
            worst = max(worst, a - start)
        else:
            start = None
    return min(worst, 360.0)


def _fringe(shape, threshold):
    core = shape.buffer(-threshold / 2.0).buffer(threshold / 2.0)
    thin = shape.difference(core)
    pieces = list(thin.geoms) if hasattr(thin, "geoms") else [thin]
    return thin.area, max((piece.area for piece in pieces), default=0.0)


def audit():
    n = P.CORONA_COUNT
    skirt = Polygon(G.skirt_outline())
    hero = Polygon(G.hero_profile())
    body = unary_union([skirt, hero])
    polar = _ring_polar(body)

    frames = [G.tongue_frame(i) for i in range(n)]
    lengths = [P.CORONA_TIPS[i]
               - 0.5 * (P.CORONA_TROUGHS[i][1] + P.CORONA_TROUGHS[(i + 1) % n][1])
               for i in range(n)]
    roots = [f["root_width"] for f in frames]
    depths = [max(P.CORONA_TIPS[i], P.CORONA_TIPS[(i - 1) % n])
              - P.CORONA_TROUGHS[i][1] for i in range(n)]
    # every tongue's two root points are the two trough floor ends it shares
    # with its neighbours, so consecutive roots meet exactly
    joins = [hypot(frames[i]["B"][0] - G.xy(*[P.CORONA_TROUGHS[(i + 1) % n][1],
                                              P.CORONA_TROUGHS[(i + 1) % n][0]
                                              - P.CORONA_TROUGHS[(i + 1) % n][2]])[0],
                   frames[i]["B"][1] - G.xy(P.CORONA_TROUGHS[(i + 1) % n][1],
                                            P.CORONA_TROUGHS[(i + 1) % n][0]
                                            - P.CORONA_TROUGHS[(i + 1) % n][2])[1])
             for i in range(n)]

    pockets = unary_union([
        Polygon(G.sector_profile(point, P.POCKET_INNER, P.POCKET_OUTER, 0.0))
        for point in range(1, P.LANES + 1)
    ])
    band = body.difference(pockets)
    band_thin, band_worst = _fringe(band, FRINGE)
    deck_thin, deck_worst = _fringe(body, FRINGE)

    interiors = (list(body.interiors) if body.geom_type == "Polygon"
                 else [ring for part in body.geoms for ring in part.interiors])
    loops = sorted((round(Polygon(ring).area, 3) for ring in interiors), reverse=True)
    bounds = body.bounds

    # the hero has to rise out of the skirt, not stand on it or replace it
    hero_root = hero.intersection(skirt).area
    hero_span = [P.HERO_START, P.HERO_START + P.HERO_SPAN]
    under_hero = [i for i in range(n)
                  if hero_span[0] < frames[i]["psi"] % 360.0 < hero_span[1]]
    troughs_under = [i for i in range(n)
                     if hero_span[0] < P.CORONA_TROUGHS[i][0] < hero_span[1]]

    # a counter at the outermost station must keep the flat support it had: the
    # notched tiles are measured against the same tiles with no notch at all
    notched = outer_counter_support(True)
    unnotched = outer_counter_support(False)

    report = {
        "kind": "rainward-corona-skirt-audit",
        "1_tongue_count": n,
        "2_longest_plain_circular_arc_deg": round(_longest_plain_run(polar), 3),
        "3_min_root_width_mm": round(min(roots), 3),
        "3_min_root_over_own_length": round(
            min(r / l for r, l in zip(roots, lengths)), 3),
        "3_max_root_join_gap_mm": round(max(joins), 6),
        "4_length_min_mm": round(min(lengths), 3),
        "4_length_max_mm": round(max(lengths), 3),
        "4_length_ratio": round(max(lengths) / min(lengths), 3),
        "4_lengths_in_order": [round(v, 2) for v in lengths],
        "5_flame_depth_sorted_mm": [round(d, 2) for d in sorted(depths, reverse=True)],
        "5_troughs_at_or_over_9mm": sum(1 for d in depths if d >= DEEP_MM),
        "6_plan_pieces": 1 if body.geom_type == "Polygon" else len(body.geoms),
        "6_body_is_valid": bool(body.is_valid and skirt.exterior.is_simple),
        "7_closed_loops": len(loops),
        "7_closed_loop_area_mm2": loops,
        "7_hero_rooted_in_skirt_mm2": round(hero_root, 2),
        "7_tongues_under_the_hero": len(under_hero),
        "7_trough_floors_under_the_hero": len(troughs_under),
        "outer_counter_support_notched": round(notched, 5),
        "outer_counter_support_if_unnotched": round(unnotched, 5),
        "outer_counter_support_lost_to_notches": round(unnotched - notched, 6),
        "narrowest_rim_under_a_lane_axis_mm": round(
            min(G.skirt_radius(G.theta(point) + step * 0.1)
                for point in range(1, P.LANES + 1) for step in range(-28, 29)), 3),
        "envelope_mm": [round(bounds[2] - bounds[0], 3),
                        round(bounds[3] - bounds[1], 3)],
        "max_radius_mm": round(max(r for _, r in polar), 3),
        "min_tip_thickness_mm": round(2 * min(f["cap"] for f in frames), 3),
        "hero_band_thickness_mm": 2 * P.HERO_HALF,
        "deck_sub_wall_area_mm2": round(deck_thin, 3),
        "deck_worst_region_mm2": round(deck_worst, 4),
        "pocket_band_sub_wall_area_mm2": round(band_thin, 3),
        "pocket_band_worst_region_mm2": round(band_worst, 4),
    }
    report["pass"] = bool(
        MIN_TONGUES <= n <= MAX_TONGUES
        and report["2_longest_plain_circular_arc_deg"] <= PLAIN_LIMIT
        and report["3_min_root_width_mm"] >= MIN_ROOT_MM
        and report["3_min_root_over_own_length"] >= MIN_ROOT_SHARE
        and report["3_max_root_join_gap_mm"] <= 1e-6
        and report["4_length_ratio"] >= MIN_LENGTH_RATIO
        and report["5_troughs_at_or_over_9mm"] >= MIN_DEEP_TROUGHS
        and report["6_plan_pieces"] == 1 and report["6_body_is_valid"]
        and report["7_closed_loops"] == 1
        and report["7_hero_rooted_in_skirt_mm2"] >= 12.0
        and report["7_tongues_under_the_hero"] >= 2
        and report["outer_counter_support_lost_to_notches"] <= 1e-6
        and max(report["envelope_mm"]) <= 194.0
        and report["min_tip_thickness_mm"] >= MIN_WALL
        and report["pocket_band_worst_region_mm2"] <= 0.10
        and report["deck_worst_region_mm2"] <= 0.10)
    return report


if __name__ == "__main__":
    result = audit()
    with open("measure/corona-skirt-audit.json", "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({k: v for k, v in result.items()
                      if k not in ("4_lengths_in_order", "5_flame_depth_sorted_mm")},
                     indent=2, sort_keys=True))
    sys.exit(0 if result["pass"] else 1)
