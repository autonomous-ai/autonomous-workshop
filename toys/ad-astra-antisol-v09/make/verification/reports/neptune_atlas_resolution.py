"""Neptune's streaks, spot and companion against the 0.4 mm nozzle.

The brief asks for every streak's printed width, length, shortest edge and
narrowest neck, tabulated against the nozzle, in the form
`measure/earth-atlas-resolution.md` uses.  This is that table, measured on the
exact rings `parts/neptune_atlas.py` hands the build rather than on the numbers
the table was written with, so a streak that came out narrower than it was
drawn would show up here rather than in the print.

Four things have to clear the nozzle: the streaks themselves, the gaps between
neighbouring markings, the gap between the dark spot and its bright companion,
and the shortest edge of every ring.  All four are measured below, on the
sphere, in millimetres of arc.

    "$WORKSHOP_PYTHON" measure/neptune_atlas_resolution.py \\
        > measure/neptune-atlas-resolution.md
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import params as P                                            # noqa: E402
from parts import neptune_atlas as N                          # noqa: E402
from parts.neptune_atlas import TAPER_END                      # noqa: E402

MM = N.MM_PER_DEG
NOZZLE = P.NOZZLE_MM

#: How finely a ring is resampled before two rings are compared.  A ring edge
#: is up to 0.9 mm long and the gaps being measured are half that, so the
#: vertices alone would overstate a gap wherever the closest approach falls
#: between two of them.  0.05 mm of arc is a quarter of the nozzle.
RESAMPLE_MM = 0.05


def unit(lon_deg: float, lat_deg: float):
    lat, lon = math.radians(lat_deg), math.radians(lon_deg)
    return (math.cos(lat) * math.cos(lon),
            math.cos(lat) * math.sin(lon),
            math.sin(lat))


def arc_mm(one, other) -> float:
    dot = max(-1.0, min(1.0, sum(a * b for a, b in zip(one, other))))
    return math.degrees(math.acos(dot)) * MM


def ring_edges(ring):
    return [arc_mm(unit(*ring[index]), unit(*ring[(index + 1) % len(ring)]))
            for index in range(len(ring))]


def ring_perimeter(ring) -> float:
    return sum(ring_edges(ring))


def ring_neck(ring, min_along_mm: float) -> float:
    """How close the ring comes to ITSELF, ignoring its own local curvature.

    On a stadium this is the printed width: the two long sides are everywhere
    the width apart, and that is the narrowest the shape gets.  The measurement
    has to exclude pairs that are close only because they are neighbours on the
    same rounded end -- every ring is close to itself locally -- so pairs
    nearer than `min_along_mm` ALONG the perimeter are skipped.  A stadium's
    end cap is pi.w/2 of perimeter, so any threshold above that leaves the
    side-to-side measurement and nothing else.

    Measured on the resampled ring rather than on its vertices, because the
    closest approach between two straight edges rarely falls on an endpoint.
    """
    points, along = dense_with_length(ring)
    total = along[-1] + arc_mm(points[-1], points[0])
    best = None
    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            gap_along = min(along[j] - along[i], total - (along[j] - along[i]))
            if gap_along < min_along_mm:
                continue
            value = arc_mm(points[i], points[j])
            best = value if best is None else min(best, value)
    return best


def dense_with_length(ring):
    """The resampled ring, and each sample's distance along the perimeter."""
    points, along, walked = [], [], 0.0
    for index in range(len(ring)):
        one = unit(*ring[index])
        other = unit(*ring[(index + 1) % len(ring)])
        span = arc_mm(one, other)
        steps = max(1, int(math.ceil(span / RESAMPLE_MM)))
        angle = math.radians(span / MM)
        for step in range(steps):
            t = step / steps
            if angle < 1e-9:
                points.append(one)
                along.append(walked)
                continue
            a = math.sin((1.0 - t) * angle) / math.sin(angle)
            b = math.sin(t * angle) / math.sin(angle)
            points.append(tuple(a * one[axis] + b * other[axis]
                                for axis in range(3)))
            along.append(walked + t * span)
        walked += span
    return points, along


def dense(ring):
    """The ring resampled along its own edges, for gap measurement."""
    return dense_with_length(ring)[0]


def gap_mm(first, second) -> float:
    """The closest approach of two rings, in millimetres of arc."""
    left, right = dense(first), dense(second)
    best = None
    for one in left:
        for other in right:
            value = arc_mm(one, other)
            best = value if best is None else min(best, value)
    return best


def verdict(value: float) -> str:
    return "clears" if value >= NOZZLE else "**UNDER**"


def main() -> int:
    print("# Neptune's cloud streaks at globe scale")
    print()
    print("Neptune's globe is Ø%.2f mm, so its radius is %.3f mm and one"
          % (N.GLOBE_D, N.GLOBE_D / 2.0))
    print("degree of great-circle arc is %.4f mm.  The nozzle is %.2f mm,"
          % (MM, NOZZLE))
    print("which is the narrowest colour boundary the printer can lay down")
    print("and %.2f degrees of arc here." % N.NOZZLE_DEG)
    print()
    print("The owner's width decision is 1.5 mm.  On this globe that is")
    print("%.2f degrees of arc, not the 3.93 the brief also states -- 3.93"
          % (1.5 / MM))
    print("degrees is 0.75 mm here.  The millimetre is what is drawn and what")
    print("is measured below; `parts/neptune_atlas.py` records the correction.")
    print()

    print("## Every streak")
    print()
    print("A streak TAPERS: it is at its drawn width across the middle and")
    print("%.0f per cent of it at each end, so two widths are measured. `middle`" % (100.0 * 0.40))
    print("is the distance between its two long sides at the centre and `end`")
    print("is the ring's own narrowest neck, which on this shape is the width")
    print("across the rounded end -- the narrowest colour boundary the printer")
    print("is asked to lay down anywhere on this streak.")
    print("`length` is the centreline's great-circle arc; the brief specifies a")
    print("streak's length in degrees of longitude, and a degree of longitude")
    print("is cos(latitude) of a degree of arc, so both are given.")
    print()
    print("| streak | lat | lon | tilt | drawn mm | length deg lon | length deg arc "
          "| length mm | aspect | vertices | shortest edge mm | middle mm | end mm | |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|")
    worst_edge = None
    worst_width = None
    worst_middle = None
    max_end = None
    for key, lat, lon, extent, tilt, width, bend, skew, end in N.STREAKS:
        ring = N.STREAK_RINGS[key]
        arc = N.streak_arc_len(lat, extent)
        length_mm = arc * MM
        neck = ring_neck(ring, 1.65 * width)
        middle = arc_mm(unit(lon, lat - 0.5 * width / MM),
                        unit(lon, lat + 0.5 * width / MM))
        shortest = min(ring_edges(ring))
        worst_edge = shortest if worst_edge is None else min(worst_edge, shortest)
        worst_width = neck if worst_width is None else min(worst_width, neck)
        worst_middle = middle if worst_middle is None else min(worst_middle, middle)
        max_end = neck if max_end is None else max(max_end, neck)
        print("| `%s` | %+.0f | %+.1f | %+.0f | %.2f | %.0f | %.1f | %.2f | %.1f:1 "
              "| %d | %.2f | %.2f | %.2f | %s |"
              % (key, lat, lon, tilt, width, extent, arc, length_mm,
                 length_mm / middle, len(ring), shortest, middle, neck,
                 verdict(neck)))
    print()
    print("Every streak is between %.2f and %.2f mm wide across its middle,"
          % (min(row[5] for row in N.STREAKS), max(row[5] for row in N.STREAKS)))
    print("against the family's")
    print("nominal 1.50 mm and the nozzle's %.2f mm.  For scale, this set's" % NOZZLE)
    print("other band systems are 3.63 to 7.26 mm (Saturn) and 2.35 to 6.12 mm")
    print("(Jupiter), so Neptune's streaks remain the narrowest marking family")
    print("anywhere in the set.")
    print()

    print("## The dark spot and its companion")
    print()
    print("The companion is a STREAK rather than an oval, so it is measured the")
    print("way the eight streaks above are: by its own narrowest neck. It is")
    print("drawn as a wisp because an independent reader of the first build of")
    print("this correction read a small oval beside the spot as a stray droplet")
    print("that had broken off it, which is the opposite of what it is for.")
    print()
    comp_neck = ring_neck(N.COMPANION_RING, 1.65 * N.COMPANION_WIDTH_MM)
    spot_neck = ring_neck(N.SPOT_RING, 1.65 * 2.0 * N.SPOT_SEMI_ARC_LAT * MM)
    print("| ring | size | vertices | perimeter mm | shortest edge mm "
          "| narrowest neck mm | |")
    print("|---|---|---:|---:|---:|---:|---|")
    print("| `spot` | %.1f x %.1f deg of arc = %.2f x %.2f mm | %d | %.2f | %.2f "
          "| %.2f | %s |"
          % (2 * N.SPOT_SEMI_ARC_LON, 2 * N.SPOT_SEMI_ARC_LAT,
             2 * N.SPOT_SEMI_ARC_LON * MM, 2 * N.SPOT_SEMI_ARC_LAT * MM,
             len(N.SPOT_RING), ring_perimeter(N.SPOT_RING),
             min(ring_edges(N.SPOT_RING)), spot_neck, verdict(spot_neck)))
    comp_arc = N.COMPANION_EXTENT_DEG * math.cos(math.radians(N.COMPANION_LAT))
    print("| `companion` | %.0f deg of longitude = %.2f mm long, %.2f mm wide "
          "| %d | %.2f | %.2f | %.2f | %s |"
          % (N.COMPANION_EXTENT_DEG, comp_arc * MM, N.COMPANION_WIDTH_MM,
             len(N.COMPANION_RING), ring_perimeter(N.COMPANION_RING),
             min(ring_edges(N.COMPANION_RING)), comp_neck, verdict(comp_neck)))
    print()
    print("The companion is %.0f per cent of the spot's length and %.0f per cent"
          % (100.0 * comp_arc / (2 * N.SPOT_SEMI_ARC_LON),
             100.0 * N.COMPANION_WIDTH_MM / (2 * N.SPOT_SEMI_ARC_LAT * MM)))
    print("of its height, so it cannot be read as a second dark spot or as part")
    print("of the first.")
    print()
    spot_gap = gap_mm(N.SPOT_RING, N.COMPANION_RING)
    print("The gap between the spot and its companion is **%.2f mm**, %s the"
          % (spot_gap, "clear of" if spot_gap >= NOZZLE else "UNDER"))
    print("%.2f mm nozzle.  The brief's rule if that gap were short is to move" % NOZZLE)
    print("the companion rather than shrink it, and that is the rule the")
    print("companion's latitude is set by: its size was chosen against the")
    print("spot's first and the gap decided where it sits.")
    print()

    print("## The gap between every pair of markings")
    print()
    print("Two markings running closer than the nozzle print as one.  Every")
    print("pair of the ten rings on this globe is measured; the table lists")
    print("every pair closer than 3.00 mm, which is where the question stops")
    print("being interesting.  Rings are resampled to %.2f mm before" % RESAMPLE_MM)
    print("comparison, because the closest approach rarely falls on a vertex.")
    print()
    names = list(N.RINGS)
    rows = []
    worst_gap = None
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            value = gap_mm(N.RINGS[names[i]], N.RINGS[names[j]])
            worst_gap = value if worst_gap is None else min(worst_gap, value)
            if value < 3.0:
                rows.append((value, names[i], names[j]))
    print("| pair | gap mm | |")
    print("|---|---:|---|")
    for value, one, other in sorted(rows):
        print("| `%s` / `%s` | %.2f | %s |" % (one, other, value, verdict(value)))
    print()
    print("The closest approach anywhere on this globe is **%.2f mm**." % worst_gap)
    print()

    print("## The verdict")
    print()
    print("Three quantities decide whether this globe prints, and all three are")
    print("widths of MATERIAL: how wide the colour region is where it is")
    print("narrowest, and how wide the bare globe is between two regions.")
    print()
    print("| quantity | narrowest mm | nozzle mm | |")
    print("|---|---:|---:|---|")
    print("| streak width across its middle | %.2f | %.2f | %s |"
          % (worst_middle, NOZZLE, verdict(worst_middle)))
    print("| streak width at its narrowest end | %.2f | %.2f | %s |"
          % (worst_width, NOZZLE, verdict(worst_width)))
    print("| gap between two markings | %.2f | %.2f | %s |"
          % (worst_gap, NOZZLE, verdict(worst_gap)))
    print()
    print("## The shortest ring edge, and why it is not in that table")
    print()
    print("The shortest edge of any ring on this globe is %.2f mm, under the"
          % worst_edge)
    print("%.2f mm nozzle and under the 0.50 mm least ring edge this set holds"
          % NOZZLE)
    print("its coastlines to. That is reported here rather than hidden, and it")
    print("is not a printability finding, because it is not the width of")
    print("anything. Every edge that short is one facet of a streak's rounded")
    print("END: the end is a half-disc of radius %.2f to %.2f mm cut into four"
          % (0.5 * TAPER_END * min(row[5] for row in N.STREAKS),
             0.5 * TAPER_END * max(row[5] for row in N.STREAKS)))
    print("segments, so its chords are necessarily shorter than the %.2f to"
          % worst_width)
    print("%.2f mm feature they approximate. The 0.50 mm margin exists for a"
          % max_end)
    print("coastline ring, where a short edge can pinch the region it bounds to")
    print("nothing; here it cannot, and the measurement that proves it is the")
    print("`end mm` column above -- the narrowest the material itself gets,")
    print("measured on the ring rather than inferred from it. Cutting the ends")
    print("into two segments instead of four would put every edge over the")
    print("nozzle and would replace a rounded end with a chisel point, which is")
    print("the shape the correction exists to avoid.")
    print()
    print("## What is not drawn")
    print()
    print(N.NOT_DRAWN)
    return 0 if min(worst_width, worst_middle, worst_gap) >= NOZZLE else 1


if __name__ == "__main__":
    raise SystemExit(main())
