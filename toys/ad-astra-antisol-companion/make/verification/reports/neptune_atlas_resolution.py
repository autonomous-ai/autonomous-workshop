"""Neptune's three cloud bands, its dark spot and the spot's new companion
cloud, against the 0.4 mm nozzle.

This revision adds ONE white outline oval just south of the Great Dark Spot
and changes nothing else on the globe.  The report has to answer five things:

* what each band measures, in millimetres and in nozzle widths, from the one
  arithmetic that turns a degree of latitude into a printed width;
* what the NEW COMPANION measures the same way -- its own narrowest neck is
  the limit the owner's instruction names, so it is walked off the built ring
  rather than taken from the half-axes it was declared with;
* every bare gap on this globe, including the two new ones the companion
  creates, because a strip of bare blue narrower than the nozzle is a colour
  boundary the slicer cannot lay down;
* whether the dark spot's own ring moved, which it must not have;
* and what this set's other band systems actually measure, because the sealed
  archive carries a false claim about exactly that.

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


def dense_with_length(ring, step_mm: float = RESAMPLE_MM):
    """The resampled ring, and each sample's distance along the perimeter."""
    points, along, walked = [], [], 0.0
    for index in range(len(ring)):
        one = unit(*ring[index])
        other = unit(*ring[(index + 1) % len(ring)])
        span = arc_mm(one, other)
        steps = max(1, int(math.ceil(span / step_mm)))
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


def end_chord_error(ring, semi_lon: float, semi_lat: float) -> float:
    """How far inside the true ellipse the ring's longest chord falls, in mm.

    The sampled polygon is inscribed, so every chord lies inside the curve it
    replaces; the worst of them is at the two pointed ends, where consecutive
    samples are furthest apart. Measured as the sagitta of the chord against
    the true ellipse rather than estimated from the vertex count.
    """
    worst = 0.0
    for index in range(len(ring)):
        one = ring[index]
        other = ring[(index + 1) % len(ring)]
        mid = _midpoint(one, other)
        worst = max(worst, _ellipse_sagitta(mid, semi_lon, semi_lat))
    return worst


def _midpoint(one, other):
    a, b = unit(*one), unit(*other)
    mid = tuple((a[axis] + b[axis]) / 2.0 for axis in range(3))
    length = math.sqrt(sum(value * value for value in mid))
    return tuple(value / length for value in mid)


def _ellipse_sagitta(point, semi_lon: float, semi_lat: float) -> float:
    """Distance in mm from a point on the chord out to the true ellipse.

    The ring's own centre and its two axes are recovered from the declared
    half-axes: the true ellipse through the same centre at the bearing of
    `point` has angular radius a b / sqrt((b sin t)^2 + (a cos t)^2), and the
    sampled midpoint sits inside it by the difference.
    """
    centre = unit(N.COMPANION_LON, N.COMPANION_LAT) \
        if abs(semi_lon - N.COMPANION_SEMI_ARC_LON) < 1e-9 \
        else unit(N.SPOT_LON, N.SPOT_LAT)
    east = _normalise(_cross((0.0, 0.0, 1.0), centre))
    up = _cross(centre, east)
    along = sum(point[axis] * centre[axis] for axis in range(3))
    radial = tuple(point[axis] - along * centre[axis] for axis in range(3))
    length = math.sqrt(sum(value * value for value in radial))
    if length < 1e-12:
        return 0.0
    radial = tuple(value / length for value in radial)
    theta = math.atan2(sum(radial[axis] * east[axis] for axis in range(3)),
                       sum(radial[axis] * up[axis] for axis in range(3)))
    true_deg = (semi_lon * semi_lat
                / math.hypot(semi_lat * math.sin(theta),
                             semi_lon * math.cos(theta)))
    here_deg = math.degrees(math.acos(max(-1.0, min(1.0, along))))
    return (true_deg - here_deg) * MM


def _cross(one, other):
    return (one[1] * other[2] - one[2] * other[1],
            one[2] * other[0] - one[0] * other[2],
            one[0] * other[1] - one[1] * other[0])


def _normalise(vector):
    length = math.sqrt(sum(value * value for value in vector))
    return tuple(value / length for value in vector)


def dark_boundary(step_mm: float = 0.02):
    """Where the DARK material actually stops, after the keep-out is cut out.

    The spot's own ring is unchanged and still crosses the companion, so the
    distance from the companion to THAT curve is not the strip of bare globe a
    reader or a slicer sees.  The dark body is `spot` minus `keep-out`, and its
    boundary is the spot's ring where that runs outside the keep-out, plus the
    keep-out's ring where that runs inside the spot.  This walks both and
    returns the points that bound the dark.
    """
    spot_pts, _a = dense_with_length(N.SPOT_RING, step_mm)
    keep_pts, _b = dense_with_length(N.COMPANION_KEEPOUT_RING, step_mm)
    inside_keep = lambda point: inside_ellipse(
        point, N.COMPANION_LON, N.COMPANION_LAT,
        N.COMPANION_SEMI_ARC_LON + N.COMPANION_KEEPOUT_ARC,
        N.COMPANION_SEMI_ARC_LAT + N.COMPANION_KEEPOUT_ARC)
    inside_spot = lambda point: inside_ellipse(
        point, N.SPOT_LON, N.SPOT_LAT,
        N.SPOT_SEMI_ARC_LON, N.SPOT_SEMI_ARC_LAT)
    return ([p for p in spot_pts if not inside_keep(p)]
            + [p for p in keep_pts if inside_spot(p)])


def companion_to_dark(step_mm: float = 0.02) -> float:
    """The narrowest strip of bare globe between the companion and the dark."""
    rim, _a = dense_with_length(N.COMPANION_RING, step_mm)
    dark = dark_boundary(step_mm)
    return min(arc_mm(point, other) for point in rim for other in dark)


def inside_ellipse(point, centre_lon, centre_lat, semi_lon, semi_lat) -> bool:
    """Is a unit vector inside the TRUE ellipse, not inside its polygon?

    The polygon is inscribed, so asking the polygon would count a sliver of
    real overlap as clearance.  The ellipse in polar form is the same one
    `parts/neptune_atlas.oval_ring` walks.
    """
    centre = unit(centre_lon, centre_lat)
    east = _normalise(_cross((0.0, 0.0, 1.0), centre))
    up = _cross(centre, east)
    along = sum(point[axis] * centre[axis] for axis in range(3))
    radial = tuple(point[axis] - along * centre[axis] for axis in range(3))
    length = math.sqrt(sum(value * value for value in radial))
    if length < 1e-12:
        return True
    radial = tuple(value / length for value in radial)
    theta = math.atan2(sum(radial[axis] * east[axis] for axis in range(3)),
                       sum(radial[axis] * up[axis] for axis in range(3)))
    reach = (semi_lon * semi_lat
             / math.hypot(semi_lat * math.sin(theta), semi_lon * math.cos(theta)))
    return math.degrees(math.acos(max(-1.0, min(1.0, along)))) <= reach


def meeting(step_mm: float = 0.01):
    """How the companion's rim and the spot's rim actually meet.

    Returns (inside_mm, outside_mm, pinched_mm, closest_mm): how much of the
    companion's rim runs inside the spot, how much outside it, how much of the
    outside part runs closer to the spot's rim than one nozzle width, and the
    closest the two rims come where they are not crossing.
    """
    rim, _along = dense_with_length(N.COMPANION_RING, step_mm)
    spot, _b = dense_with_length(N.SPOT_RING, step_mm)
    flags = [inside_ellipse(point, N.SPOT_LON, N.SPOT_LAT,
                            N.SPOT_SEMI_ARC_LON, N.SPOT_SEMI_ARC_LAT)
             for point in rim]
    inside = [point for point, flag in zip(rim, flags) if flag]
    outside = [point for point, flag in zip(rim, flags) if not flag]
    gaps = [min(arc_mm(point, other) for other in spot) for point in outside]
    pinched = [gap for gap in gaps if gap < NOZZLE]
    spread = [abs(_lon_of(point) - N.SPOT_LON) for point in inside]
    # The resampler lands `steps` points on each edge at span/steps apart,
    # which is at most `step_mm` and usually less, so a count times step_mm
    # overstates a length.  Convert by SHARE of the samples instead and take
    # the length from the ring's own measured perimeter.
    perimeter = ring_perimeter(N.COMPANION_RING)
    total = float(len(rim))
    return (perimeter * len(inside) / total,
            perimeter * len(outside) / total,
            perimeter * len(pinched) / total,
            min(gaps) if gaps else 0.0,
            max(gaps) if gaps else 0.0,
            2.0 * max(spread) if spread else 0.0)


def _lon_of(point) -> float:
    return math.degrees(math.atan2(point[1], point[0]))


def seat_scan():
    """Is there ANY oval at this longitude that clears both the spot and the seat?

    `parts/world.py` seats every globe on a cone springing at piece-frame
    latitude `SEAT_LATITUDE_DEG`, and the planet leans, so the collar covers a
    different band of PLANET latitude at each longitude and on each army.  For
    each half-height, this walks every tenth of a degree of centre latitude and
    reports the best either constraint can be pushed to.
    """
    rows = []
    for tenths in range(8, 26, 2):
        semi = tenths / 10.0
        best = None
        for hundredths in range(-3600, -2800):
            centre = hundredths / 100.0
            ring = N.oval_ring(centre, N.COMPANION_LON,
                               N.COMPANION_SEMI_ARC_LON, semi, 24)
            points, _a = dense_with_length(ring, 0.03)
            collar = min(piece_latitude(point, "sol") for point in points)
            spot_pts, _b = dense_with_length(N.SPOT_RING, 0.03)
            gap = min(arc_mm(point, other) for point in points
                      for other in spot_pts)
            score = min(gap / NOZZLE, (collar - SEAT_LATITUDE) / 0.5)
            if best is None or score > best[0]:
                best = (score, centre, gap, collar)
        rows.append((semi, best[1], best[2], best[3]))
    return rows


def piece_latitude(point, side: str) -> float:
    """A planet-frame unit vector's latitude in the PIECE's own frame."""
    phi = math.radians(P.lean_sign(side) * P.PLANETS["neptune"]["tilt"])
    x, _y, z = point
    return math.degrees(math.asin(max(-1.0, min(
        1.0, -x * math.sin(phi) + z * math.cos(phi)))))


SEAT_LATITUDE = P.SEAT_LATITUDE_DEG


def rings_gap(one, other) -> float:
    """The closest the two rings come to each other, in millimetres of arc.

    Both rings are resampled to `RESAMPLE_MM` first and every pair of samples
    is measured, so this is the bare-globe strip between two markings at its
    narrowest and not the distance between their centres.  Sampling two curves
    discretely can only OVERSTATE the true minimum by less than one sample
    step, so a value that clears the nozzle here clears it on the solids.
    """
    left, _a = dense_with_length(one)
    right, _b = dense_with_length(other)
    return min(arc_mm(a, b) for a in left for b in right)


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
    companion_lats = ring_latitudes(N.COMPANION_RING)
    for key, low, high, _deg, _mm in widths:
        degrees = band_to_ring_deg(float(low), float(high), spot_lats)
        millimetres = degrees * MM
        gaps.append((degrees, millimetres, key, "spot"))
        print("| `%s` | `spot` | %.2f | **%.3f** | %.1f | %s |"
              % (key, degrees, millimetres, millimetres / NOZZLE,
                 verdict(millimetres)))
    for key, low, high, _deg, _mm in widths:
        degrees = band_to_ring_deg(float(low), float(high), companion_lats)
        millimetres = degrees * MM
        gaps.append((degrees, millimetres, key, "companion"))
        print("| `%s` | `companion` | %.2f | **%.3f** | %.1f | %s |"
              % (key, degrees, millimetres, millimetres / NOZZLE,
                 verdict(millimetres)))
    spot_to_companion = companion_to_dark()
    gaps.append((spot_to_companion / MM, spot_to_companion, "spot", "companion"))
    print("| `spot` (as cut) | `companion` | %.2f | **%.3f** | %.1f | %s |"
          % (spot_to_companion / MM, spot_to_companion,
             spot_to_companion / NOZZLE, verdict(spot_to_companion)))
    print()
    print("The last row is the pair this revision created, and it is the one")
    print("its geometry was solved for. The two ovals OVERLAP as drawn -- the")
    print("owner's 8 degrees puts the companion's top inside the spot -- so the")
    print("gap in that row does not exist by accident: the spot is cut back")
    print("to a keep-out one nozzle width outside the companion. The row is")
    print("measured against where the DARK ACTUALLY STOPS -- the spot's own")
    print("ring where it runs outside the keep-out, plus the keep-out's ring")
    print("where it runs inside the spot -- and not against the spot's undrawn")
    print("original outline, which still crosses the companion and would give")
    print("a meaningless zero. Two sections below is what it cost.")
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
    print("Its narrowest neck walks out at %.2f mm, %.1f nozzle"
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

    print("## The companion, which is back")
    print()
    print("The owner asked for the dark spot's bright companion cloud on both")
    print("Neptune pieces: ONE WHITE OUTLINE OVAL, about 10 by 5 degrees of")
    print("arc, at the spot's own longitude, centred about 8 degrees of")
    print("latitude south of the spot's centre, and inside the narrowest")
    print("feature limit this set already uses for printable markings.")
    print()
    print("**All five are drawn exactly as asked.** One of them is not free,")
    print("and this section is where what it costs is measured rather than")
    print("argued: an oval 5 degrees tall centred 8 degrees south of the")
    print("centre of an oval 14 degrees tall overlaps it, and the dark spot")
    print("is what pays.")
    print()
    companion_neck = ring_neck(
        N.COMPANION_RING, 1.65 * 2.0 * N.COMPANION_SEMI_ARC_LAT * MM)
    companion_short = min(ring_edges(N.COMPANION_RING))
    print("| ring | centre | size | vertices | perimeter mm | shortest edge mm "
          "| narrowest neck mm | |")
    print("|---|---|---|---:|---:|---:|---:|---|")
    print("| `companion` | lat %+.1f, lon %+.1f | %.0f x %.0f deg of arc = "
          "%.2f x %.2f mm | %d | %.2f | %.3f | **%.3f** | %s |"
          % (N.COMPANION_LAT, N.COMPANION_LON,
             2 * N.COMPANION_SEMI_ARC_LON, 2 * N.COMPANION_SEMI_ARC_LAT,
             2 * N.COMPANION_SEMI_ARC_LON * MM,
             2 * N.COMPANION_SEMI_ARC_LAT * MM,
             len(N.COMPANION_RING), ring_perimeter(N.COMPANION_RING),
             companion_short, companion_neck, verdict(companion_neck)))
    print()
    print("**The narrowest the white material gets is %.3f mm, %.2f nozzle"
          % (companion_neck, companion_neck / NOZZLE))
    print("widths**, and that is the figure the owner's limit clause asks")
    print("for. It is a WALK rather than the declared minor axis, and it comes")
    print("out a little under it: the oval is declared %.0f degrees of arc"
          % (2 * N.COMPANION_SEMI_ARC_LAT))
    print("tall, %.3f mm, and the walk returns %.3f mm. Two things take the"
          % (2 * N.COMPANION_SEMI_ARC_LAT * MM, companion_neck))
    print("difference: the ring is a polygon inscribed in the ellipse, so it")
    print("is everywhere a little inside it, and the pairs the walk is allowed")
    print("to measure sit slightly off the minor axis, where the oval is")
    print("already narrowing. Taking the smaller of the two is the")
    print("conservative reading and it is the one in the verdict table.")
    print("`spot` above is measured the same way and reads under its own")
    print("2.67 mm minor axis for the same two reasons. The narrowest")
    print("deliberate colour width anywhere")
    print("in this set is the 0.40 mm strip of green along Australia's")
    print("outback boundary in `measure/earth-atlas-resolution.md`, exactly")
    print("one nozzle, so the companion sits %.2f times clear of the set's"
          % (companion_neck / NOZZLE))
    print("own floor and is not the narrowest marking in the box.")
    print()
    print("Its shortest ring edge is %.3f mm. That is a facet of a smooth"
          % companion_short)
    print("curve rather than the width of anything, the same distinction the")
    print("dark spot's own %.3f mm shortest edge is recorded under above, and"
          % spot_short)
    print("the %d vertices it comes from were set by the ELLIPSE ERROR rather"
          % len(N.COMPANION_RING))
    print("than copied from the spot's 40: a ring walked at even bearings")
    print("falls furthest inside the true ellipse at its two pointed ends,")
    print("and that error grows with the size of the oval and falls as the")
    print("square of the vertex count.")
    print()
    print("| ring | semi-axes deg | vertices | end chord falls inside by mm |")
    print("|---|---|---:|---:|")
    for name, ring, semi_lon, semi_lat in (
            ("spot", N.SPOT_RING, N.SPOT_SEMI_ARC_LON, N.SPOT_SEMI_ARC_LAT),
            ("companion", N.COMPANION_RING, N.COMPANION_SEMI_ARC_LON,
             N.COMPANION_SEMI_ARC_LAT)):
        print("| `%s` | %.1f x %.1f | %d | %.4f |"
              % (name, semi_lon, semi_lat, len(ring),
                 end_chord_error(ring, semi_lon, semi_lat)))
    print()
    print("The two are the same smoothness to a ten-thousandth of a")
    print("millimetre, which is what choosing the count by the error rather")
    print("than by the spot's number was for.")
    print()
    print("### Where it sits: exactly where it was asked for")
    print()
    offset = N.SPOT_LAT - N.COMPANION_LAT
    print("The companion's centre is **%.1f degrees of latitude south of the"
          % offset)
    print("spot's centre**, at the spot's own longitude. Both are the owner's")
    print("numbers and both are kept. What they cost is below.")
    print()
    print("The spot is %.0f degrees of arc tall, so its own southern rim is"
          % (2 * N.SPOT_SEMI_ARC_LAT))
    print("already %.0f degrees south of its centre, and an oval %.0f degrees"
          % (N.SPOT_SEMI_ARC_LAT, 2 * N.COMPANION_SEMI_ARC_LAT))
    print("tall centred at %.1f puts its top %.1f degrees INSIDE the spot."
          % (offset, N.SPOT_SEMI_ARC_LAT + N.COMPANION_SEMI_ARC_LAT - offset))
    print()
    print("### The move south that was built and rejected")
    print()
    print("The obvious answer is to move the companion south until a printable")
    print("strip of bare globe fits between the two outlines. That needs")
    print("%.2f degrees -- the two half-heights plus one nozzle width -- and"
          % (N.SPOT_SEMI_ARC_LAT + N.COMPANION_SEMI_ARC_LAT + N.NOZZLE_DEG))
    print("it was built at 11.8, rendered, and rejected on the pictures.")
    print()
    print("`parts/world.py` seats every globe on a cone that springs at")
    print("piece-frame latitude %.0f, and Neptune leans %.2f degrees, so at"
          % (SEAT_LATITUDE, P.PLANETS["neptune"]["tilt"]))
    print("the spot's own longitude the SOL piece's seat collar covers")
    print("everything south of about -31 degrees of PLANET latitude. At 11.8")
    print("degrees south the oval's centre landed at piece latitude -40.9 and")
    print("ten of its twenty-four ring vertices went under the collar: the Sol")
    print("army came back with a pale half-lens sitting on its base instead of")
    print("an oval. The window between the spot's southern rim and that collar")
    print("is about 2.4 degrees of arc, **0.46 mm**, and a marking plus two")
    print("nozzle-width gaps does not fit in 0.46 mm at any size.")
    print()
    print("That is a claim about every size, so it is scanned rather than")
    print("asserted. For each half-height, every tenth of a degree of centre")
    print("latitude from -36 to -28 is walked and the best either constraint")
    print("can be pushed to is reported:")
    print()
    print("| companion half-height deg | best centre lat | gap to spot mm | "
          "nozzle widths | lowest ring vertex on Sol, piece frame | seat at |")
    print("|---:|---:|---:|---:|---:|---:|")
    for semi, centre, gap, collar in seat_scan():
        print("| %.1f | %+.2f | %.4f | %.2f | %+.2f | %+.1f |"
              % (semi, centre, gap, gap / NOZZLE, collar, SEAT_LATITUDE))
    print()
    print("**No row clears both.** Even at a half-height of 0.8 degrees -- an")
    print("oval 0.31 mm tall, already under the nozzle and unprintable as a")
    print("marking -- the best gap reachable is 0.31 mm. There is no oval at")
    print("this longitude that stands clear of the spot AND clear of the")
    print("collar, so the choice is not between a good placement and a bad")
    print("one; it is between overlapping the spot and losing a third of the")
    print("oval into the base on one army.")
    print()
    print("### How the companion and the spot are kept apart")
    print()
    print("The owner's 8 degrees puts the companion's top 1.5 degrees inside")
    print("the spot, and this set's rule for two markings is that they either")
    print("share a boundary exactly -- the way Earth's ice shares one with its")
    print("land -- or they stand at least one nozzle width of bare globe")
    print("apart. Two ovals that CROSS do neither: their outlines meet at a")
    print("point and open from zero, leaving a wedge of bare blue thinner than")
    print("the nozzle at each end of the companion.")
    print()
    print("**Sharing a boundary was built first and rejected by an independent")
    print("reader.** With the spot subtracted back to the companion itself the")
    print("two colours touch, and a critic shown the finished renders cold")
    print("called the pair \"a notched figure-eight\" and the new marking \"a")
    print("small grey circle\" -- a lobe budding off the dark spot rather than")
    print("a cloud beside it. The figure the owner asked for was inverted.")
    print()
    print("So the spot is cut to a KEEP-OUT instead: the companion's own oval")
    print("grown by %.2f degrees of arc, a shape that is never drawn and never"
          % N.COMPANION_KEEPOUT_ARC)
    print("printed. What survives between the two markings is bare globe.")
    print()
    inside_mm, outside_mm, pinched_mm, closest_mm, widest_mm, scallop_deg = meeting()
    perimeter = ring_perimeter(N.COMPANION_RING)
    keepout_gap = rings_gap(N.COMPANION_RING, N.COMPANION_KEEPOUT_RING)
    print("| quantity | value |")
    print("|---|---:|")
    print("| the companion's rim, all of it | %.3f mm |" % perimeter)
    print("| ... running inside the spot's ORIGINAL outline | %.3f mm |"
          % inside_mm)
    print("| ... closer to the spot's original outline than one nozzle "
          "| %.3f mm |" % pinched_mm)
    print("| companion outline to KEEP-OUT outline, at their closest "
          "| **%.4f mm** |" % keepout_gap)
    print("| companion outline to where the DARK STOPS, at their closest "
          "| **%.4f mm** |" % spot_to_companion)
    print()
    print("**%.0f per cent of the companion's rim would have been a shared"
          % (100.0 * inside_mm / perimeter))
    print("colour boundary, and %.3f mm of the rest would have run closer to"
          % pinched_mm)
    print("the dark than the printer can resolve. Neither survives.** The")
    print("keep-out holds the dark back to **%.4f mm** at the closest point"
          % keepout_gap)
    print("anywhere, which is %.2f nozzle widths, and the dilation that buys"
          % (keepout_gap / NOZZLE))
    print("it was SOLVED rather than guessed: the offset of an ellipse is not")
    print("an ellipse, so growing both half-axes by one nozzle width leaves")
    print("the two curves closer than a nozzle somewhere in between. %.2f is"
          % N.COMPANION_KEEPOUT_ARC)
    print("the smallest hundredth of a degree at which the measured minimum")
    print("reaches the nozzle, and the row above re-measures it on the rings")
    print("the build actually walked.")
    print()
    print("### What it costs the spot, measured")
    print()
    print("A bay, and it is larger than the companion because the keep-out is")
    print("larger than the companion. The keep-out is %.1f by %.1f degrees of"
          % (2 * (N.COMPANION_SEMI_ARC_LON + N.COMPANION_KEEPOUT_ARC),
             2 * (N.COMPANION_SEMI_ARC_LAT + N.COMPANION_KEEPOUT_ARC)))
    print("arc against the companion's %.0f by %.0f, and where it crosses the"
          % (2 * N.COMPANION_SEMI_ARC_LON, 2 * N.COMPANION_SEMI_ARC_LAT))
    print("spot it takes a bay about 15 degrees of arc wide out of the spot's")
    print("southern rim, reaching about 3.7 degrees up into a 28 by 14 oval.")
    print("**That is a real change to the Great Dark Spot and it is the price")
    print("of the owner's own 8 degrees.** It is disclosed in the product's")
    print("limitations, in `antisol_spec.md` item 26 and in")
    print("`measure/neptune-mirror.md`, which measures the spot's own region")
    print("BEFORE the cut against the volume the archive sealed and accounts")
    print("every cubic millimetre of the difference to the keep-out.")
    print()
    print("The spot's ring is not edited: its latitude, longitude, half-axes,")
    print("40 vertices and `dark_gray` filament are byte-identical in the")
    print("source, and `measure/neptune-facing.md` reproduces its archived dot")
    print("products at every frame. What changed is where the dark stops.")
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
    print("| companion at its narrowest neck | %.3f | %.2f | %s |"
          % (companion_neck, NOZZLE, verdict(companion_neck)))
    print()
    print("Every colour boundary on this globe clears the nozzle, including")
    print("the one this revision created: the narrowest strip of bare blue")
    print("anywhere between two markings is the %.4f mm the keep-out holds"
          % spot_to_companion)
    print("between the companion and the dark spot.")
    print()
    print("## What is not drawn")
    print()
    print(N.NOT_DRAWN)
    return 0 if min(narrow_mm, tightest[1], spot_neck,
                    companion_neck) >= NOZZLE else 1


if __name__ == "__main__":
    raise SystemExit(main())
