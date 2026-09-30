"""What Mercury's outlines cost on the smallest globe in the set.

The sibling of `measure/atlas_resolution.py` and `measure/mars_atlas_resolution.py`,
in the same form and answering the same question one globe further down the
ladder: which features survive a 0.4 mm nozzle when one degree of arc is
0.120 mm.  Mercury is Ø13.78 mm, so the nozzle is 3.33 degrees of arc here
against 2.74 on Earth and 2.63 on Mars -- every angle costs more on this ball
than on any other in the set.

Five things have to clear the nozzle, and all five are measured below on the
sphere, in millimetres of arc, on the exact rings `parts/mercury_atlas.py`
hands the build:

* every ring's own edges and necks;
* the gray channel between two plains that do not fuse;
* the Caloris rim annulus, which is what is left when the floor is subtracted
  out of the outer ring and is the narrowest deliberate feature on the piece;
* the gray strip between a plain's southern boundary and latitude -42, where
  the seat cone springs and the visible sphere ends;
* the gray between Caloris and the nearest plain.

Two of them are peculiar to this world.  The rings are generated from a
formula rather than carried as survey data, so the vertex count is chosen
against each ring's own least radius rather than fixed -- that rule is in
`parts/mercury_atlas.vertex_count`, and this report is where it is checked.
And unlike Earth and Mars, several of Mercury's plains are *meant* to fuse:
the reference shows the smooth plains running together, so a pair whose
boundaries cross is the right answer and only a pair that comes close without
crossing is a fault.

    "$WORKSHOP_PYTHON" measure/mercury_atlas_resolution.py \\
        > measure/mercury-atlas-resolution.md
"""

from __future__ import annotations

import itertools
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import params as P                                            # noqa: E402
from parts import mercury_atlas as M                          # noqa: E402

PLANET = "mercury"
R = P.globe_radius(PLANET)
NOZZLE = P.NOZZLE_MM
MM_PER_DEG = math.radians(1.0) * R

#: Where the seat cone springs, from `params.SEAT_LATITUDE_DEG`.  South of it
#: the ball is buried inside the collar it stands on and nothing is visible.
SEAT_LAT = P.SEAT_LATITUDE_DEG

#: How finely a region's boundary is walked for the separation measurements.
SWEEP = 1440


def unit(lon_deg: float, lat_deg: float):
    lat, lon = math.radians(lat_deg), math.radians(lon_deg)
    return (math.cos(lat) * math.cos(lon), math.cos(lat) * math.sin(lon),
            math.sin(lat))


def dot(one, other):
    return sum(a * b for a, b in zip(one, other))


def cross(one, other):
    return (one[1] * other[2] - one[2] * other[1],
            one[2] * other[0] - one[0] * other[2],
            one[0] * other[1] - one[1] * other[0])


def norm(vector):
    length = math.sqrt(dot(vector, vector))
    return tuple(value / length for value in vector)


def arc(one, other) -> float:
    """Great-circle distance between two unit vectors, in mm of arc."""
    return R * math.atan2(math.sqrt(dot(cross(one, other), cross(one, other))),
                          dot(one, other))


def arc_to_segment(point, start, end) -> float:
    axis = cross(start, end)
    if dot(axis, axis) < 1e-18:
        return arc(point, start)
    axis = norm(axis)
    foot = tuple(point[index] - dot(point, axis) * axis[index] for index in range(3))
    if dot(foot, foot) < 1e-18:
        return min(arc(point, start), arc(point, end))
    foot = norm(foot)
    span = arc(start, end)
    if arc(start, foot) <= span + 1e-9 and arc(foot, end) <= span + 1e-9:
        return arc(point, foot)
    return min(arc(point, start), arc(point, end))


def ring_vectors(ring):
    return [unit(lon, lat) for lon, lat in ring]


def edges(vectors):
    return [(vectors[index], vectors[(index + 1) % len(vectors)])
            for index in range(len(vectors))]


def perimeter(vectors) -> float:
    return sum(arc(one, other) for one, other in edges(vectors))


def shortest_edge(vectors) -> float:
    return min(arc(one, other) for one, other in edges(vectors))


def narrowest_neck(vectors) -> float:
    """The closest a vertex comes to an edge it is not an endpoint of."""
    count = len(vectors)
    worst = float("inf")
    for index, point in enumerate(vectors):
        for other in range(count):
            if other == index or (other + 1) % count == index:
                continue
            worst = min(worst, arc_to_segment(point, vectors[other],
                                              vectors[(other + 1) % count]))
    return worst


# ---------------------------------------------------------------- regions ---
#: Every region as the star shape it is: centre, mean radius and lobes.  The
#: rings above are this evaluated at a finite number of bearings; separations
#: are measured on the continuous form so the answer does not depend on where
#: a vertex happened to land.
REGIONS = {name: (lat, lon, radius, lobes)
           for name, lat, lon, radius, lobes in M.PLAINS_SPECS}
REGIONS["caloris_rim"] = (M.CALORIS_LAT, M.CALORIS_LON,
                          M.CALORIS_RIM_RADIUS, M.CALORIS_RIM_LOBES)
REGIONS["caloris_floor"] = (M.CALORIS_LAT, M.CALORIS_LON,
                            M.CALORIS_FLOOR_RADIUS, M.CALORIS_FLOOR_LOBES)


def _basis(name: str):
    lat, lon, _radius, _lobes = REGIONS[name]
    centre = unit(lon, lat)
    east = norm(cross((0.0, 0.0, 1.0), centre))
    return centre, east, cross(centre, east)


def radius_at(name: str, bearing: float) -> float:
    _lat, _lon, radius, lobes = REGIONS[name]
    return radius * (1.0 + sum(
        amplitude * math.cos(harmonic * bearing - math.radians(phase))
        for harmonic, amplitude, phase in lobes))


def walk(name: str, steps: int = SWEEP):
    centre, east, up = _basis(name)
    out = []
    for index in range(steps):
        bearing = -2.0 * math.pi * index / steps
        reach = math.radians(radius_at(name, bearing))
        out.append(tuple(
            math.cos(reach) * centre[axis]
            + math.sin(reach) * (math.cos(bearing) * up[axis]
                                 + math.sin(bearing) * east[axis])
            for axis in range(3)))
    return out


def signed_gap(name: str, point) -> float:
    """Degrees from the region's boundary: positive outside, negative inside."""
    centre, east, up = _basis(name)
    away = math.acos(max(-1.0, min(1.0, dot(centre, point))))
    across = tuple(point[axis] - math.cos(away) * centre[axis] for axis in range(3))
    if dot(across, across) < 1e-18:
        return -radius_at(name, 0.0)
    across = norm(across)
    bearing = math.atan2(dot(across, east), dot(across, up))
    return math.degrees(away) - radius_at(name, bearing)


def separation(one: str, other: str) -> float:
    """Least signed gap between two regions, in degrees."""
    return min(min(signed_gap(other, point) for point in walk(one)),
               min(signed_gap(one, point) for point in walk(other)))


def main() -> int:
    failures: list[str] = []

    print("# Mercury's albedo atlas at globe scale")
    print()
    print("Mercury's globe is Ø%.2f mm, the smallest in the set, so its radius"
          % P.globe_diameter(PLANET))
    print("is %.3f mm and one degree of arc is %.4f mm.  The nozzle is %.2f mm,"
          % (R, MM_PER_DEG, NOZZLE))
    print("which is the narrowest colour boundary the printer can lay down and")
    print("%.2f degrees of arc here -- against 2.74 degrees on Earth and 2.63 on"
          % (NOZZLE / MM_PER_DEG))
    print("Mars, the other two worlds drawn from outlines.")
    print()

    print("## Every ring")
    print()
    print("The vertex count is not fixed. `parts/mercury_atlas.vertex_count`")
    print("takes the most vertices a ring can carry with every edge still at or")
    print("above %.2f mm, measured against that ring's own least radius, so a"
          % M.MIN_EDGE_MM)
    print("strongly lobed plain gets fewer and larger steps and a nearly round")
    print("one gets more. This table is where that rule is checked rather than")
    print("trusted.")
    print()
    print("| ring | vertices | perimeter mm | shortest edge mm | narrowest neck mm |")
    print("|---|---|---|---|---|")
    for name in sorted(M.RINGS):
        vectors = ring_vectors(M.RINGS[name])
        edge, neck = shortest_edge(vectors), narrowest_neck(vectors)
        print("| %s | %d | %.2f | %.2f | %.2f |"
              % (name, len(vectors), perimeter(vectors), edge, neck))
        if min(edge, neck) < NOZZLE:
            failures.append("%s: shortest edge %.2f mm, narrowest neck %.2f mm"
                            % (name, edge, neck))
    print()

    print("## The gray between two plains")
    print()
    print("Unlike Earth's coastlines and Mars's maria, several of these are")
    print("*meant* to run together: the reference shows the smooth plains fusing")
    print("into larger regions rather than sitting apart as separate discs. A")
    print("pair whose boundaries cross is therefore the intended answer and is")
    print("listed as fused. Only a pair that comes close without crossing can")
    print("leave a channel of bare gray too thin to print.")
    print()
    print("| pair | gap | reads as |")
    print("|---|---|---|")
    names = M.PLAIN_NAMES + ["caloris_rim"]
    for one, other in itertools.combinations(names, 2):
        gap = separation(one, other)
        if gap > 12.0:
            continue
        if gap < 0.0:
            verdict = "fused, overlapping by %.2f mm" % (-gap * MM_PER_DEG)
        else:
            verdict = "%.2f mm of gray between them" % (gap * MM_PER_DEG)
            if gap * MM_PER_DEG < NOZZLE:
                failures.append("%s and %s leave %.2f mm of gray"
                                % (one, other, gap * MM_PER_DEG))
        print("| %s / %s | %+.2f deg | %s |" % (one, other, gap, verdict))
    print()
    print("Every pair not listed is more than %.2f mm apart."
          % (12.0 * MM_PER_DEG))
    print()

    print("## The Caloris rim annulus")
    print()
    print("The rim is what is left when the floor's radial cone is subtracted")
    print("out of the outer ring, so its width is the difference between two")
    print("scalloped outlines and is the narrowest deliberate feature on this")
    print("piece. Both outlines are irregular on purpose -- a true circle at")
    print("this size reads as a drilled hole -- so the width is swept rather")
    print("than assumed.")
    print()
    widths = [-signed_gap("caloris_rim", point)
              for point in walk("caloris_floor")]
    print("| measure | degrees | mm |")
    print("|---|---|---|")
    print("| narrowest | %.2f | %.3f |" % (min(widths), min(widths) * MM_PER_DEG))
    print("| mean | %.2f | %.3f |"
          % (sum(widths) / len(widths), sum(widths) / len(widths) * MM_PER_DEG))
    print("| widest | %.2f | %.3f |" % (max(widths), max(widths) * MM_PER_DEG))
    print("| the basin across, outer mean | %.2f | %.3f |"
          % (2 * M.CALORIS_RIM_RADIUS, 2 * M.CALORIS_RIM_RADIUS * MM_PER_DEG))
    print("| the floor across, mean | %.2f | %.3f |"
          % (2 * M.CALORIS_FLOOR_RADIUS, 2 * M.CALORIS_FLOOR_RADIUS * MM_PER_DEG))
    print()
    if min(widths) * MM_PER_DEG < NOZZLE:
        failures.append("the Caloris rim narrows to %.3f mm"
                        % (min(widths) * MM_PER_DEG))
    print("Caloris is about 1550 km across on a planet 4879 km in diameter,")
    print("which is 36 degrees of arc and %.2f mm here, the number the outer"
          % (2 * M.CALORIS_RIM_RADIUS * MM_PER_DEG))
    print("ring is drawn to.")
    print()

    print("## The gray between a plain and the seat")
    print()
    print("The globe is sunk into its disc and carried by a seat cone that")
    print("springs at latitude %.0f, so everything south of that parallel is"
          % SEAT_LAT)
    print("buried inside the collar and invisible. A plain whose southern")
    print("boundary lands in the %.2f degrees just north of it would leave a"
          % (NOZZLE / MM_PER_DEG))
    print("strip of bare gray under the nozzle, so every ring is held clear.")
    print()
    print("| ring | southernmost boundary | clear of the seat by |")
    print("|---|---|---|")
    for name in M.PLAIN_NAMES:
        south = min(math.degrees(math.asin(max(-1.0, min(1.0, point[2]))))
                    for point in walk(name))
        clear = south - SEAT_LAT
        print("| %s | %+.2f deg | %.2f deg = %.2f mm |"
              % (name, south, clear, clear * MM_PER_DEG))
        if 0.0 < clear * MM_PER_DEG < NOZZLE:
            failures.append("%s leaves %.2f mm of gray above the seat"
                            % (name, clear * MM_PER_DEG))
    print()

    print("## What the atlas does not draw")
    print()
    print("- **Craters.** %s" % M.CRATERS_NOT_DRAWN)
    print()

    print("## Simplifications")
    print()
    if M.SIMPLIFIED:
        for name in sorted(M.SIMPLIFIED):
            print("- **%s** -- %s" % (name, M.SIMPLIFIED[name]))
    else:
        print("None.")
    print()

    print("## Verdict")
    print()
    if failures:
        print("Under the nozzle, and therefore unprintable as drawn:")
        print()
        for item in failures:
            print("- %s" % item)
    else:
        print("Nothing in Mercury's atlas falls under the %.2f mm nozzle at this"
              % NOZZLE)
        print("globe size: no ring edge, no neck, no gray channel between two")
        print("plains, no part of the Caloris rim annulus, and no strip between a")
        print("plain and the seat the globe stands on. The seven plains keep the")
        print("seven centres the round-patch build used.")
    print()
    print("Measured by `measure/mercury_atlas_resolution.py` on the exact rings")
    print("in `parts/mercury_atlas.py`.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
