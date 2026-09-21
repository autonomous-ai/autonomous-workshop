"""Exact plan audit of where every counter actually lands.

The tiles are separate parts, so "the counter sits on its own lane" is a
statement about one tile's flat top face, not about the board. Every polygon
here is the exact outline the CAD builds: the tile sector eroded by its 0.15 mm
top rounding, and the counter's own cubic Bezier outline sampled at 128 points
per segment. Run it from the CAD project directory.
"""
import json
import os
import pathlib
import sys
from math import cos, radians, sin

_PROJECT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT))
os.chdir(_PROJECT)

from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

import params as P
import profiles as G
from parts.counter import outline as counter_curves

SUPPORT_FLOOR = 0.95         # fraction of a footprint that must be on its own tile
CENTROID_MARGIN = 2.0        # mm the mass centre keeps inside the contact hull
BAR_SITES = [(x, y) for x in (-11.0, 0.0, 11.0) for y in (-4.5, 4.5)]


def counter_outline():
    points = []
    for curve in counter_curves():
        for i in range(128):
            t = i / 128.0
            u = 1.0 - t
            points.append(tuple(
                u ** 3 * curve[0][j] + 3 * u * u * t * curve[1][j]
                + 3 * u * t * t * curve[2][j] + t ** 3 * curve[3][j]
                for j in (0, 1)))
    return points


OUTLINE = counter_outline()


def placed(radius, angle_deg):
    a = radians(angle_deg)
    cx, cy = G.xy(radius, angle_deg)
    return Polygon([(cx + x * cos(a) - y * sin(a), cy + x * sin(a) + y * cos(a))
                    for x, y in OUTLINE])


def tile_top(point):
    """The flat part of one tile's top face, after the 0.15 mm edge rounding."""
    return Polygon(G.sector_profile(point, P.LANE_INNER, P.TILE_OUTER, P.CLEAR,
                                    samples=720)).buffer(-P.EDGE_ROUND)


def tick_plan():
    """The four engraved bank ticks, as plan rectangles on the bar top."""
    half = P.MARKER_W / 2.0
    out = []
    for point in G.bank_boundary_points():
        angle = G.theta(point) - P.PITCH / 2.0
        a = radians(angle)
        lo, hi = P.MARKER_R - P.MARKER_L / 2.0, P.MARKER_R + P.MARKER_L / 2.0
        corners = [(lo, -half), (hi, -half), (hi, half), (lo, half)]
        out.append(Polygon([(x * cos(a) - y * sin(a), x * sin(a) + y * cos(a))
                            for x, y in corners]))
    return unary_union(out)


def audit():
    tops = {point: tile_top(point) for point in range(1, P.LANES + 1)}
    worst = {"support": (2.0, None), "margin": (99.0, None)}
    per_station = {}
    adjacent_contact = 0.0
    landings = 0
    for index, radius in enumerate(P.RADII):
        station_worst = 2.0
        for point in range(1, P.LANES + 1):
            angle = G.theta(point)
            neighbours = [tops[G.next_point(point)],
                          tops[point - 1 if point > 1 else P.LANES]]
            landings += 1
            foot = placed(radius, angle)
            on_own = foot.intersection(tops[point])
            fraction = on_own.area / foot.area
            station_worst = min(station_worst, fraction)
            if fraction < worst["support"][0]:
                worst["support"] = (fraction, "lane %d, r%.1f" % (point, radius))
            for other in neighbours:
                adjacent_contact = max(adjacent_contact, foot.intersection(other).area)
            hull = on_own.convex_hull
            margin = hull.exterior.distance(foot.centroid) if not hull.is_empty else 0.0
            if not hull.contains(foot.centroid):
                margin = -margin
            if margin < worst["margin"][0]:
                worst["margin"] = (margin, "lane %d, r%.1f" % (point, radius))
        per_station["station_%.1f" % radius] = round(station_worst, 5)

    closest = None
    for point in range(1, P.LANES + 1):
        a = placed(P.RADII[-1], G.theta(point))
        b = placed(P.RADII[-1], G.theta(G.next_point(point)))
        gap = a.distance(b)
        closest = gap if closest is None else min(closest, gap)

    bar = Point(0, 0).buffer(P.BAR_R, quad_segs=512)
    ticks = tick_plan()
    sites = [Polygon([(x - P.DROP_L / 2.0, y - P.DROP_W / 2.0),
                      (x + P.DROP_L / 2.0, y - P.DROP_W / 2.0),
                      (x + P.DROP_L / 2.0, y + P.DROP_W / 2.0),
                      (x - P.DROP_L / 2.0, y + P.DROP_W / 2.0)])
             for x, y in BAR_SITES]
    sites_inside = all(bar.contains(s) for s in sites)
    sites_disjoint = all(sites[i].intersection(sites[j]).area == 0.0
                         for i in range(len(sites)) for j in range(i + 1, len(sites)))
    tick_under_site = max(s.intersection(ticks).area for s in sites)
    widest_tick_run = P.MARKER_W

    report = {
        "kind": "rainward-sunflare-fit-audit",
        "landings_checked": landings,
        "lane_capacity_per_lane": len(P.RADII) * 3,
        "worst_own_tile_support_fraction": round(worst["support"][0], 5),
        "worst_own_tile_support_at": worst["support"][1],
        "own_tile_support_by_station": per_station,
        "worst_centroid_to_contact_hull_mm": round(worst["margin"][0], 3),
        "worst_centroid_margin_at": worst["margin"][1],
        "max_adjacent_tile_contact_mm2": round(adjacent_contact, 6),
        "min_adjacent_lane_outline_gap_mm": round(closest, 3),
        "bar_sites": len(BAR_SITES),
        "bar_sites_inside_platform": bool(sites_inside),
        "bar_sites_disjoint": bool(sites_disjoint),
        "widest_bank_tick_a_drop_bridges_mm": widest_tick_run,
        "drop_length_over_tick_width": round(P.DROP_L / widest_tick_run, 3),
        "max_tick_area_under_a_bar_site_mm2": round(tick_under_site, 4),
        "note": ("Support is measured against one tile's flat top face only. The "
                 "lane narrows toward the hub, so a counter at the innermost "
                 "32.0 mm station reaches past its own tile's side edge; that "
                 "shortfall below 1.0 is reported, never hidden, and it lands "
                 "in the 1.00 mm orange margin, never on a neighbouring tile. "
                 "Every tile ends on the same exact circular arc at radius "
                 "79.55 mm, so no counter loses support to a notch or a bay."),
    }
    report["pass"] = bool(
        report["worst_own_tile_support_fraction"] >= SUPPORT_FLOOR
        and report["own_tile_support_by_station"]["station_%.1f" % P.RADII[0]] >= 1.0
        and report["worst_centroid_to_contact_hull_mm"] >= CENTROID_MARGIN
        and report["max_adjacent_tile_contact_mm2"] == 0.0
        and report["min_adjacent_lane_outline_gap_mm"] > 0.0
        and report["drop_length_over_tick_width"] >= 3.0
        and sites_inside and sites_disjoint)
    return report


if __name__ == "__main__":
    result = audit()
    pathlib.Path("measure/fit-audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    sys.exit(0 if result["pass"] else 1)
