"""Neptune's three cloud bands and its dark spot against the 0.4 mm nozzle.

This revision puts Neptune's three closed white latitude bands back and takes
the eight short streaks and the spot's bright companion away.  The report has
to answer four things:

* what each band measures, in millimetres and in nozzle widths, from the one
  arithmetic that turns a degree of latitude into a printed width;
* the widest bare gap between two of them, and the narrowest gap anywhere;
* whether the dark spot's own contribution moved, which it must not have;
* and what this set's other band systems actually measure, because the sealed
  archive carries a false claim about exactly that and this run rewrites the
  report the claim is in.

THE ARITHMETIC, DERIVED RATHER THAN QUOTED.  A great circle of a sphere of
diameter d is pi*d long and 360 degrees round, so one degree of great-circle
arc is pi*d/360.  On Neptune's globe, d = 21.89 mm, that is 0.1910 mm.  It is
NOT pi*d/180, which is 0.3821 mm and twice the truth.  That exact factor of
two is in the sealed archive already -- see "The three figures this report
corrects" below -- so it is derived here in the open, once, and every figure
in this report comes from it.

THE CROSS-WORLD FIGURES ARE READ, NOT TYPED.  Saturn's and Jupiter's band
widths are parsed out of `measure/saturn-atlas-resolution.md` and
`measure/jupiter-atlas-resolution.md` at run time, so the comparison below is
this set's own measurement of those worlds rather than a number copied by
hand.  Copying them by hand is what went wrong last time.

    "$WORKSHOP_PYTHON" measure/neptune_atlas_resolution.py \\
        > measure/neptune-atlas-resolution.md
"""

from __future__ import annotations

import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import params as P                                            # noqa: E402
from parts import neptune_atlas as N                          # noqa: E402

MM = N.MM_PER_DEG
NOZZLE = P.NOZZLE_MM

#: How finely a ring is resampled before a distance is taken off it.
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


def ring_neck(ring, min_along_mm: float) -> float:
    """How close the ring comes to ITSELF, ignoring its own local curvature.

    Pairs nearer than `min_along_mm` along the perimeter are skipped, because
    every ring is close to itself locally.  On the spot's ellipse this returns
    the minor axis, which is the narrowest the dark material gets.
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


def ring_latitudes(ring):
    """Every sampled latitude of a ring, resampled, in degrees."""
    points, _along = dense_with_length(ring)
    return [math.degrees(math.asin(max(-1.0, min(1.0, point[2]))))
            for point in points]


def band_to_ring_deg(low: float, high: float, latitudes) -> float:
    """Closest approach in degrees between a latitude band and a ring.

    A band is a full circle of latitude, so the shortest path from any point
    to it runs along that point's own meridian -- which crosses every parallel
    square -- and is exactly the difference in latitude.  Longitude cannot
    shorten it and cannot lengthen it.
    """
    return min(0.0 if low <= lat <= high else min(abs(lat - low), abs(lat - high))
               for lat in latitudes)


def verdict(value: float) -> str:
    return "clears" if value >= NOZZLE else "**UNDER**"


# ------------------------------------------------- this set's own reports ---
def table_rows(path: Path, heading: str):
    """Every data row of the first markdown table under `heading`."""
    lines = path.read_text().splitlines()
    start = next(i for i, line in enumerate(lines) if line.strip() == heading)
    rows, seen_header = [], False
    for line in lines[start + 1:]:
        stripped = line.strip()
        if not stripped.startswith("|"):
            if rows:
                break
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if not seen_header:
            seen_header = True
            header = cells
            continue
        if all(set(cell) <= set("-: ") for cell in cells):
            continue
        rows.append(dict(zip(header, cells)))
    return rows


def number(cell: str) -> float:
    return float(re.sub(r"[^0-9.+-]", "", cell))


def narrowest(path: Path, heading: str, column: str, label: str):
    """(name, millimetres) of the narrowest row of one report's table."""
    rows = table_rows(path, heading)
    best = min(rows, key=lambda row: number(row[column]))
    return best[label].strip("` "), number(best[column])


def main() -> int:
    saturn_report = HERE / "saturn-atlas-resolution.md"
    jupiter_report = HERE / "jupiter-atlas-resolution.md"
    saturn_name, saturn_mm = narrowest(
        saturn_report, "## The five bands", "width mm", "band")
    jupiter_belt_name, jupiter_belt_mm = narrowest(
        jupiter_report, "## The six belts", "least mm", "belt")
    jupiter_zone_name, jupiter_zone_mm = narrowest(
        jupiter_report, "## The five zones", "least mm", "zone")
    jupiter_globe_d = P.globe_diameter("jupiter")
    jupiter_mm_per_deg = math.radians(1.0) * jupiter_globe_d / 2.0

    print("# Neptune's three cloud bands at globe scale")
    print()
    print("Neptune's globe is Ø%.2f mm, so its radius is %.3f mm."
          % (N.GLOBE_D, N.GLOBE_R))
    print()
    print("A great circle of a sphere of diameter d is pi*d long and 360")
    print("degrees round, so ONE DEGREE OF GREAT-CIRCLE ARC IS pi*d/360.")
    print("Here that is pi * %.2f / 360 = **%.4f mm**. It is not pi*d/180,"
          % (N.GLOBE_D, MM))
    print("which would give %.4f mm and is twice the truth; that doubling is"
          % (math.pi * N.GLOBE_D / 180.0))
    print("already in this set's sealed archive and the last section of this")
    print("report is about it. Every figure below comes from the %.4f."  % MM)
    print()
    print("The nozzle is %.2f mm, the narrowest colour boundary the printer"
          % NOZZLE)
    print("can lay down, and **%.2f degrees of arc** on this globe."
          % N.NOZZLE_DEG)
    print()

    print("## The three bands")
    print()
    print("Each band is a plain `band` region: `features/patches.latitude_band_tool`")
    print("draws a torus that meets the globe's own sphere exactly at the two")
    print("edge latitudes, so a band declared n degrees wide is n degrees of")
    print("arc wide on the printed surface, at every longitude. No taper, no")
    print("bow, no tilt and no end: a closed circle of latitude has none.")
    print()
    print("| band | latitudes | width deg | width mm | nozzle widths | |")
    print("|---|---|---:|---:|---:|---|")
    widths = []
    for key, low, high in N.BANDS:
        degrees = float(high - low)
        millimetres = degrees * MM
        widths.append((key, low, high, degrees, millimetres))
        print("| `%s` | %+d to %+d | %.0f | **%.3f** | %.2f | %s |"
              % (key, low, high, degrees, millimetres,
                 millimetres / NOZZLE, verdict(millimetres)))
    print()
    narrow_key, _lo, _hi, narrow_deg, narrow_mm = min(widths, key=lambda row: row[4])
    print("The narrowest is `%s` at %.0f degrees, **%.3f mm**, %.2f nozzle"
          % (narrow_key, narrow_deg, narrow_mm, narrow_mm / NOZZLE))
    print("widths. It clears the %.2f mm nozzle, so **no band was widened**;" % NOZZLE)
    print("the three are exactly the three the build carried before the cloud")
    print("correction, at the latitudes it recorded for them.")
    print()

    print("## The gaps between them")
    print()
    print("Bare globe has to print too: a strip of globe narrower than the")
    print("nozzle is a colour boundary the slicer cannot resolve. A band is a")
    print("full circle of latitude, so the distance from anything to it runs")
    print("along that thing's own meridian and IS the difference in latitude --")
    print("longitude can neither shorten nor lengthen it.")
    print()
    print("| from | to | gap deg | gap mm | nozzle widths | |")
    print("|---|---|---:|---:|---:|---|")
    gaps = []
    for (k1, _l1, h1, _d1, _m1), (k2, l2, _h2, _d2, _m2) in zip(widths, widths[1:]):
        degrees = float(l2 - h1)
        millimetres = degrees * MM
        gaps.append((degrees, millimetres, k1, k2))
        print("| `%s` | `%s` | %.0f | **%.3f** | %.1f | %s |"
              % (k1, k2, degrees, millimetres, millimetres / NOZZLE,
                 verdict(millimetres)))

    spot_lats = ring_latitudes(N.SPOT_RING)
    for key, low, high, _deg, _mm in widths:
        degrees = band_to_ring_deg(float(low), float(high), spot_lats)
        millimetres = degrees * MM
        gaps.append((degrees, millimetres, key, "spot"))
        print("| `%s` | `spot` | %.2f | **%.3f** | %.1f | %s |"
              % (key, degrees, millimetres, millimetres / NOZZLE,
                 verdict(millimetres)))
    print()
    widest = max(gaps[:len(widths) - 1])
    tightest = min(gaps)
    print("**The widest bare gap between two of the bands is %.0f degrees, "
          "%.3f mm**" % (widest[0], widest[1]))
    print("-- the whole of the southern mid-latitudes and the tropics between")
    print("`%s` and `%s`, which is %.0f per cent of the globe's own"
          % (widest[2], widest[3], 100.0 * widest[0] / 180.0))
    print("pole-to-pole span. The tightest gap anywhere on this globe is")
    print("%.2f degrees, **%.3f mm**, between `%s` and `%s`: %.1f nozzle widths"
          % (tightest[0], tightest[1], tightest[2], tightest[3],
             tightest[1] / NOZZLE))
    print("of bare blue.")
    print()

    print("## The dark spot, which did not move")
    print()
    print("The owner's instruction is that the dark spot stays exactly as the")
    print("build this revision corrects has it. Nothing here was edited, and")
    print("this table is the check rather than the claim: the ring is walked")
    print("again from `parts/neptune_atlas.SPOT_RING` and measured.")
    print()
    spot_neck = ring_neck(N.SPOT_RING, 1.65 * 2.0 * N.SPOT_SEMI_ARC_LAT * MM)
    spot_short = min(ring_edges(N.SPOT_RING))
    print("| ring | centre | size | vertices | perimeter mm | shortest edge mm "
          "| narrowest neck mm | |")
    print("|---|---|---|---:|---:|---:|---:|---|")
    print("| `spot` | lat %+.0f, lon %+.1f | %.0f x %.0f deg of arc = %.2f x %.2f mm "
          "| %d | %.2f | %.3f | **%.2f** | %s |"
          % (N.SPOT_LAT, N.SPOT_LON,
             2 * N.SPOT_SEMI_ARC_LON, 2 * N.SPOT_SEMI_ARC_LAT,
             2 * N.SPOT_SEMI_ARC_LON * MM, 2 * N.SPOT_SEMI_ARC_LAT * MM,
             len(N.SPOT_RING), ring_perimeter(N.SPOT_RING), spot_short,
             spot_neck, verdict(spot_neck)))
    print()
    print("Its narrowest neck is its own minor axis, %.2f mm, %.1f nozzle"
          % (spot_neck, spot_neck / NOZZLE))
    print("widths. Its shortest edge is %.3f mm, under the nozzle and under"
          % spot_short)
    print("the 0.50 mm least ring edge this set holds its coastlines to; that")
    print("is one facet of a smooth curve rather than the width of anything,")
    print("and the 40 vertices it comes from are what an independent reader of")
    print("a 22-vertex version of this oval asked for. The measurement that")
    print("matters for printing is the neck, and it is in the table.")
    print()
    print("The spot's SOLID contribution is the check that it did not move, and")
    print("it is taken on the built colour bodies rather than here.")
    print("`measure/neptune-mirror.md` measures the `spot` body on both armies")
    print("and compares it against the volume the archived build measured; that")
    print("is the number requirement 2 of this revision turns on.")
    print()

    print("## The companion, which is gone")
    print()
    print("The build this revision corrects drew a small bright cloud beside")
    print("the spot's upper rim. It was `white`, and the marking key in this")
    print("set is the filament, so it was one of the nine bodies of the white")
    print("cloud marking. Reverting that marking to the three bands takes it")
    print("with it, and the drawing being reverted to did not have one.")
    print()
    print("`ref/neptune-sol.png` does show a bright companion cloud beside the")
    print("dark spot and this revision does not draw one. That is a deliberate")
    print("loss, recorded in the product's limitations in those terms rather")
    print("than left to be found.")
    print()

    print("## The three figures this report corrects")
    print()
    print("The sealed archive's copy of this report said, in the paragraph")
    print("beginning \"Every streak is between 1.35 and 1.65 mm wide\", that")
    print("this set's other band systems are \"3.63 to 7.26 mm (Saturn) and")
    print("2.35 to 6.12 mm (Jupiter)\", and concluded that Neptune's streaks")
    print("were \"the narrowest marking family anywhere in the set\".")
    print()
    print("Both figures are wrong and the conclusion drawn from them is wrong.")
    print("They came out of the same pi*d/180 doubling the head of this report")
    print("derives against, and the run that wrote them had caught that exact")
    print("error in its own width figure two paragraphs earlier and repeated")
    print("the owner's companion figures without recomputing them.")
    print()
    print("Read back out of this set's own reports at run time, not typed:")
    print()
    print("| claim in the sealed report | this set's own measurement | |")
    print("|---|---|---|")
    print("| Saturn's bands are 3.63 to 7.26 mm | `measure/saturn-atlas-resolution.md` "
          "measures the narrowest, the %s, at **%.2f mm** | 3.63 is exactly "
          "twice %.2f |" % (saturn_name, saturn_mm, saturn_mm))
    print("| Jupiter's belts are 2.35 to 6.12 mm | `measure/jupiter-atlas-resolution.md` "
          "measures the narrowest belt, the %s, at **%.2f mm**, and the narrowest "
          "zone, the %s, at **%.2f mm** | 2.35 is exactly twice %.2f |"
          % (jupiter_belt_name, jupiter_belt_mm, jupiter_zone_name,
             jupiter_zone_mm, jupiter_belt_mm))
    print("| Neptune's markings are the narrowest marking family in the set | "
          "the streaks that claim described were 1.35 to 1.65 mm, WIDER than "
          "Jupiter's %.2f mm belt and %.2f mm zone | **the claim was false of "
          "the streaks even at the correct numbers** |"
          % (jupiter_belt_mm, jupiter_zone_mm))
    print()
    print("### Where the comparison falls now, from the measurement")
    print()
    floor = min(saturn_mm, jupiter_belt_mm, jupiter_zone_mm)
    print("Neptune's three bands measure %s mm."
          % ", ".join("%.3f" % row[4] for row in widths))
    print("The narrowest band system anywhere else in this set is Jupiter's")
    print("%s at %.2f mm; Saturn's narrowest band is %.2f mm and Jupiter's"
          % (jupiter_zone_name, jupiter_zone_mm, saturn_mm))
    print("narrowest belt %.2f mm." % jupiter_belt_mm)
    print()
    if narrow_mm < floor:
        print("**So Neptune's bands ARE now the narrowest band family in the")
        print("set, by a factor of %.2f against the next narrowest.** That is"
              % (floor / narrow_mm))
        print("the opposite of how the comparison fell for the streaks the")
        print("sealed report was describing, and it is stated from the")
        print("measurement rather than from the revision brief. In degrees it")
        print("is not even close: Neptune's bands are %.0f to %.0f degrees of arc,"
              % (min(row[3] for row in widths), max(row[3] for row in widths)))
        print("and Jupiter's narrowest zone is %.1f on a globe %.0f per cent"
              % (jupiter_zone_mm / jupiter_mm_per_deg,
                 100.0 * (jupiter_globe_d / N.GLOBE_D - 1.0)))
        print("larger, so Neptune loses twice over -- narrower in angle and")
        print("smaller in radius.")
    else:
        print("**So Neptune's bands are NOT the narrowest band family in the")
        print("set**: the narrowest of them is %.3f mm against %.2f mm."
              % (narrow_mm, floor))
    print()
    print("One thing this does NOT make Neptune, and the distinction is worth")
    print("keeping because the sealed claim lost it: narrowest BAND family is")
    print("not narrowest marking of any kind. `measure/earth-atlas-resolution.md`")
    print("records a strip of green along Australia's outback boundary at")
    print("0.40 mm, exactly one nozzle, which is the narrowest deliberate")
    print("colour width anywhere in this set. Neptune's %.3f mm band is the"
          % narrow_mm)
    print("narrowest thing that runs the whole way round a globe.")
    print()

    print("## The verdict")
    print()
    print("| quantity | narrowest mm | nozzle mm | |")
    print("|---|---:|---:|---|")
    print("| band width | %.3f | %.2f | %s |"
          % (narrow_mm, NOZZLE, verdict(narrow_mm)))
    print("| bare globe between two markings | %.3f | %.2f | %s |"
          % (tightest[1], NOZZLE, verdict(tightest[1])))
    print("| dark spot at its narrowest neck | %.2f | %.2f | %s |"
          % (spot_neck, NOZZLE, verdict(spot_neck)))
    print()
    print("## What is not drawn")
    print()
    print(N.NOT_DRAWN)
    return 0 if min(narrow_mm, tightest[1], spot_neck) >= NOZZLE else 1


if __name__ == "__main__":
    raise SystemExit(main())
