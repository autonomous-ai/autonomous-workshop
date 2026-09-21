"""Exact plan audit of where every counter actually lands.

The tiles are separate parts now, so "the counter sits on its own lane" is a
statement about one tile's flat top face, not about the board. Every polygon
here is the exact outline the CAD builds: the tile sector eroded by its 0.15 mm
top rounding, and the counter's own cubic Bezier outline sampled at 128 points
per segment. Run it from the CAD project directory.
"""
import json
import sys
from math import cos, radians, sin

import os
import pathlib
import sys

_PROJECT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT))
os.chdir(_PROJECT)

from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

import params as P
import profiles as G
from parts.counter import FORK_CURVES, SINGLE_CURVES

SUPPORT_FLOOR = 0.90         # fraction of a footprint that must be on its own tile
CENTROID_MARGIN = 2.0        # mm the mass centre keeps inside the contact hull


def counter_outline(curves):
    points = []
    for curve in curves:
        for i in range(128):
            t = i / 128.0
            u = 1.0 - t
            points.append(tuple(
                u ** 3 * curve[0][j] + 3 * u * u * t * curve[1][j]
                + 3 * u * t * t * curve[2][j] + t ** 3 * curve[3][j]
                for j in (0, 1)))
    return points


OUTLINES = {"single": counter_outline(SINGLE_CURVES),
            "fork": counter_outline(FORK_CURVES)}


def placed(kind, radius, angle_deg):
    a = radians(angle_deg)
    cx, cy = G.xy(radius, angle_deg)
    return Polygon([(cx + x * cos(a) - y * sin(a), cy + x * sin(a) + y * cos(a))
                    for x, y in OUTLINES[kind]])


def tile_top(point):
    """The flat part of one tile's top face, after the 0.15 mm edge rounding."""
    outline = Polygon(G.sector_profile(point, P.LANE_INNER, P.TILE_OUTER, P.CLEAR,
                                       samples=720))
    return outline.buffer(-P.EDGE_ROUND)


def audit():
    tops = {point: tile_top(point) for point in range(1, P.LANES + 1)}
    marker = unary_union([
        Polygon([G.xy(r, G.theta(point) - P.PITCH / 2.0 + d)
                 for r, d in ((P.MARKER_R - P.MARKER_L / 2.0, -0.6),
                              (P.MARKER_R + P.MARKER_L / 2.0, -0.6),
                              (P.MARKER_R + P.MARKER_L / 2.0, 0.6),
                              (P.MARKER_R - P.MARKER_L / 2.0, 0.6))])
        for point in G.bank_boundary_points()])

    worst = {"support": (2.0, None), "margin": (99.0, None)}
    adjacent_contact = 0.0
    marker_contact = 0.0
    landings = 0
    for point in range(1, P.LANES + 1):
        angle = G.theta(point)
        neighbours = [tops[G.next_point(point)],
                      tops[point - 1 if point > 1 else P.LANES]]
        for radius in P.RADII:
            for kind in ("single", "fork"):
                landings += 1
                foot = placed(kind, radius, angle)
                on_own = foot.intersection(tops[point])
                fraction = on_own.area / foot.area
                if fraction < worst["support"][0]:
                    worst["support"] = (fraction, "lane %d, r%.0f, %s" % (point, radius, kind))
                for other in neighbours:
                    adjacent_contact = max(adjacent_contact, foot.intersection(other).area)
                marker_contact = max(marker_contact, foot.intersection(marker).area)
                hull = on_own.convex_hull
                margin = hull.exterior.distance(foot.centroid) if not hull.is_empty else 0.0
                if not hull.contains(foot.centroid):
                    margin = -margin
                if margin < worst["margin"][0]:
                    worst["margin"] = (margin, "lane %d, r%.0f, %s" % (point, radius, kind))

    # closest approach between counters on neighbouring lanes at the inner station
    closest = None
    for point in range(1, P.LANES + 1):
        for a_kind in ("single", "fork"):
            for b_kind in ("single", "fork"):
                a = placed(a_kind, P.RADII[-1], G.theta(point))
                b = placed(b_kind, P.RADII[-1], G.theta(G.next_point(point)))
                gap = a.distance(b)
                closest = gap if closest is None else min(closest, gap)

    # the centre bar's six preserved 12 x 8 sites stay inside the platform
    sites = [(x, y) for x in (-12.0, 0.0, 12.0) for y in (-5.0, 5.0)]
    bar = Point(0, 0).buffer(P.BAR_R, quad_segs=512)
    site_polygons = [Polygon([(x - P.DROP_L / 2.0, y - P.DROP_W / 2.0),
                              (x + P.DROP_L / 2.0, y - P.DROP_W / 2.0),
                              (x + P.DROP_L / 2.0, y + P.DROP_W / 2.0),
                              (x - P.DROP_L / 2.0, y + P.DROP_W / 2.0)])
                     for x, y in sites]
    sites_inside = all(bar.contains(s) for s in site_polygons)
    sites_disjoint = all(
        site_polygons[i].intersection(site_polygons[j]).area == 0.0
        for i in range(len(sites)) for j in range(i + 1, len(sites)))

    rim_under_counter = min(
        G.skirt_radius(G.theta(point) + step * 0.1)
        for point in range(1, P.LANES + 1) for step in range(-40, 41))

    report = {
        "kind": "rainward-corona-fit-audit",
        "min_rim_radius_under_an_outer_counter_mm": round(rim_under_counter, 3),
        "rim_note": ("Reported over the whole 8 degree band around each lane "
                     "axis. Support itself is measured on the exact counter "
                     "outlines below and is the verdict."),
        "landings_checked": landings,
        "lane_capacity_per_lane": len(P.RADII) * 3,
        "worst_own_tile_support_fraction": round(worst["support"][0], 5),
        "worst_own_tile_support_at": worst["support"][1],
        "worst_centroid_to_contact_hull_mm": round(worst["margin"][0], 3),
        "worst_centroid_margin_at": worst["margin"][1],
        "max_adjacent_tile_contact_mm2": round(adjacent_contact, 6),
        "max_marker_footprint_contact_mm2": round(marker_contact, 6),
        "min_adjacent_lane_outline_gap_mm": round(closest, 3),
        "bar_sites_inside_platform": bool(sites_inside),
        "bar_sites_disjoint": bool(sites_disjoint),
        "note": ("Support is measured against one tile's flat top face only. A "
                 "counter tail may overhang the boundary; that overhang is the "
                 "shortfall below 1.0 and is reported, never hidden. Every tile "
                 "now ends on the same exact circular arc at radius 89.85, so "
                 "no counter loses any support to a notch, a bay or a "
                 "shortened tile end."),
    }
    report["pass"] = bool(
        report["worst_own_tile_support_fraction"] >= SUPPORT_FLOOR
        and report["worst_centroid_to_contact_hull_mm"] >= CENTROID_MARGIN
        and report["max_adjacent_tile_contact_mm2"] == 0.0
        and report["max_marker_footprint_contact_mm2"] == 0.0
        and report["min_adjacent_lane_outline_gap_mm"] > 0.0
        and sites_inside and sites_disjoint)
    return report


if __name__ == "__main__":
    result = audit()
    with open("measure/fit-audit.json", "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    sys.exit(0 if result["pass"] else 1)
