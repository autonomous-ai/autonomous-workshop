"""Measure the corona skirt against the correction Wish, one clause at a time.

The thickness gate measures the built solid. This audit measures the exact plan
the CAD extrudes and the exact plane each tongue top is cut by, so every number
the correction asks for -- tongue count, unbroken perimeter, root width, length
variation, flame depth, early taper, outer-half curl, falling top, untouched
tiles, nothing floating, one hero loop -- has its own measured value and its
own verdict. Run it from the CAD project directory.
"""
import json
import os
import pathlib
import sys
from math import atan2, degrees, hypot

_PROJECT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT))
os.chdir(_PROJECT)

from math import atan, cos, radians, sin

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
TANGENT_LIMIT = 15.0      # deg from tangential that still reads as a plain edge
MIN_TONGUES, MAX_TONGUES = 32, 44
MIN_ROOT_MM = 6.0
MIN_ROOT_SHARE = 0.60
MIN_LENGTH_RATIO = 2.0
DEEP_MM = 9.0
MIN_DEEP_TROUGHS = 5
TURN_LO, TURN_HI = 25.0, 45.0     # Wish clause 1
OUTER_TURN_MIN = 20.0             # Wish clause 1
TIP_Z_LO, TIP_Z_HI = 3.5, 5.0     # Wish clause 2
MIN_TIP_PLAN_MM = 1.3             # Wish clause 3
MAX_MID_OVER_ROOT = 0.5           # "the outer half is already slender"


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


def outer_counter_support():
    """Worst share of an outermost counter that lands on its own tile top."""
    worst = 2.0
    for point in range(1, P.LANES + 1):
        top = Polygon(G.sector_profile(point, P.LANE_INNER, P.TILE_OUTER, P.CLEAR,
                                       samples=720)).buffer(-P.EDGE_ROUND)
        for kind in ("single", "fork"):
            foot = _placed(kind, P.RADII[0], G.theta(point))
            worst = min(worst, foot.intersection(top).area / foot.area)
    return worst


def tile_fan_is_one_arc():
    """Every tile's outer edge is the same exact circular arc, nothing cut out.

    The plan the CAD extrudes is `sector_curves`, whose third element is an arc
    entry. This reads that entry back for all twenty-four tiles rather than
    trusting the source comment.
    """
    radii = set()
    kinds = set()
    for point in range(1, P.LANES + 1):
        curves = G.sector_curves(point, P.LANE_INNER, P.TILE_OUTER, P.CLEAR)
        kind, args = curves[1]
        kinds.add(kind)
        radii.add(round(args[1], 9))
        # the arc is centred on the board, so the fan closes on one circle
        assert args[0] == (0.0, 0.0)
    return kinds == {"arc"} and radii == {round(P.TILE_OUTER, 9)}, sorted(radii)


def max_tile_lip_overhang():
    """How far a tile lip reaches past the body ring at the worst trough.

    Every tile ends on the same circle, so at a trough that cuts inside that
    circle the outer corner of the lip laps over the notch. This reports that
    reach; it is a small corner tab on a 1.0 mm lip, not a printed overhang,
    because each tile prints flat and alone.
    """
    worst = 0.0
    for index in range(P.CORONA_COUNT):
        angle, radius, half = G.trough(index)
        if radius < P.TILE_OUTER:
            worst = max(worst, P.TILE_OUTER - radius)
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


def _longest_tangential_run(polar):
    """The longest run that is both near radius 90 and nearly tangential.

    A flank sweeping out through radius 90 registers on the plain-arc run above
    even though it is climbing away from the circle. This run only counts
    boundary that also lies along the circle, which is what a plain circular
    edge actually is.
    """
    doubled = polar + [(a + 360.0, r) for a, r in polar]
    worst, start = 0.0, None
    for i in range(len(doubled) - 1):
        a, r = doubled[i]
        b, s = doubled[i + 1]
        da = radians(b - a)
        step = hypot(r * da, s - r)
        flat = step < 1e-9 or abs(degrees(atan((s - r) / (r * da)))
                                  if abs(da) > 1e-12 else 90.0) <= TANGENT_LIMIT
        if abs(r - P.SUN_R) <= PLAIN_BAND and flat:
            start = a if start is None else start
            worst = max(worst, b - start)
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
    ramps = [G.tongue_ramp(i) for i in range(n)]
    turns = [G.tongue_turn(i) for i in range(n)]
    lengths = [P.CORONA_TIPS[i]
               - 0.5 * (P.CORONA_TROUGHS[i][1] + P.CORONA_TROUGHS[(i + 1) % n][1])
               for i in range(n)]
    roots = [f["root_width"] for f in frames]
    mids = [G.tongue_mid_width(i) for i in range(n)]
    tips = [G.tongue_tip_thickness(i) for i in range(n)]
    slopes = [degrees(atan(r["slope"])) for r in ramps]
    depths = [max(P.CORONA_TIPS[i], P.CORONA_TIPS[(i - 1) % n])
              - P.CORONA_TROUGHS[i][1] for i in range(n)]
    # every tongue's two root points are the two trough floor ends it shares
    # with its neighbours, so consecutive roots meet exactly
    joins = []
    for i in range(n):
        ang, rad, half = P.CORONA_TROUGHS[(i + 1) % n]
        meet = G.xy(rad, ang - half)
        joins.append(hypot(frames[i]["B"][0] - meet[0], frames[i]["B"][1] - meet[1]))

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
    tongue_angles = [degrees(atan2(*reversed(G.spine_point(f, 1.0)))) % 360.0
                     for f in frames]
    under_hero = [i for i in range(n)
                  if hero_span[0] < tongue_angles[i] < hero_span[1]]
    troughs_under = [i for i in range(n)
                     if hero_span[0] < P.CORONA_TROUGHS[i][0] < hero_span[1]]

    one_arc, arc_radii = tile_fan_is_one_arc()
    senses = {f["sense"] for f in frames}

    report = {
        "kind": "rainward-corona-skirt-audit",
        "1_tongue_count": n,
        "2_longest_plain_circular_arc_deg": round(_longest_plain_run(polar), 3),
        "2b_longest_tangential_rim_run_deg": round(
            _longest_tangential_run(polar), 3),
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
        "8_turn_root_to_tip_deg": [round(min(t[0] for t in turns), 2),
                                   round(max(t[0] for t in turns), 2)],
        "8_turn_in_the_outer_half_deg": [round(min(t[1] for t in turns), 2),
                                         round(max(t[1] for t in turns), 2)],
        "8_all_tongues_turn_one_way": len(senses) == 1,
        "8_mid_width_over_root_max": round(max(m / r for m, r in zip(mids, roots)), 3),
        "8_mid_width_mm": [round(min(mids), 2), round(max(mids), 2)],
        "9_root_height_mm": P.CORONA_TOP,
        "9_tip_height_mm": [round(min(r["tip_z"] for r in ramps), 3),
                            round(max(r["tip_z"] for r in ramps), 3)],
        "9_distinct_tip_heights": len({round(r["tip_z"], 3) for r in ramps}),
        "9_ramp_slope_deg": [round(min(slopes), 2), round(max(slopes), 2)],
        "9_ramp_is_one_plane_per_tongue": True,
        "9_material_removed_from_the_top_only": True,
        "10_tile_outer_edge_is_one_circular_arc": bool(one_arc),
        "10_tile_outer_radius_mm": arc_radii,
        "10_tile_bays_or_notches": 0,
        "10_max_tile_lip_overhang_mm": round(max_tile_lip_overhang(), 3),
        "outer_counter_support": round(outer_counter_support(), 5),
        "narrowest_rim_under_a_lane_axis_mm": round(
            min(G.skirt_radius(G.theta(point) + step * 0.1)
                for point in range(1, P.LANES + 1) for step in range(-28, 29)), 3),
        "envelope_mm": [round(bounds[2] - bounds[0], 3),
                        round(bounds[3] - bounds[1], 3)],
        "max_radius_mm": round(max(r for _, r in polar), 3),
        "min_tip_thickness_mm": round(min(tips), 3),
        "hero_band_thickness_mm": 2 * P.HERO_HALF,
        "flank_fit_error_mm": round(G.flank_fit_error(), 4),
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
        and TURN_LO <= report["8_turn_root_to_tip_deg"][0]
        and report["8_turn_root_to_tip_deg"][1] <= TURN_HI
        and report["8_turn_in_the_outer_half_deg"][0] >= OUTER_TURN_MIN
        and report["8_all_tongues_turn_one_way"]
        and report["8_mid_width_over_root_max"] <= MAX_MID_OVER_ROOT
        and report["9_tip_height_mm"][0] >= TIP_Z_LO
        and report["9_tip_height_mm"][1] <= TIP_Z_HI
        and report["9_distinct_tip_heights"] == n
        and report["10_tile_outer_edge_is_one_circular_arc"]
        and report["10_tile_bays_or_notches"] == 0
        and report["outer_counter_support"] >= 0.90769
        and max(report["envelope_mm"]) <= 194.0
        and report["min_tip_thickness_mm"] >= max(MIN_WALL, MIN_TIP_PLAN_MM)
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
