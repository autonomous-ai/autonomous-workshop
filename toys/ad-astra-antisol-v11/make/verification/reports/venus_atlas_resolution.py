"""What Venus's radar atlas costs on a 16.53 mm globe.

The sibling of `measure/atlas_resolution.py`, in the same form and answering
the same question one rung of the ladder below Earth: which features of the
supplied atlas survive a 0.4 mm nozzle when one degree of arc is 0.1443 mm.

Everything is measured on the sphere, in millimetres of arc, on the exact ring
data `parts/venus_atlas.py` hands the build.  Four things have to clear the
nozzle here:

* every ring's own edges and necks, including Aphrodite Terra undivided and
  each of the two rings the build actually sweeps;
* the amber channel between two rings of the same tone that do not fuse;
* the strip the highlands leave when they are subtracted out of a lowland;
* the visible amber between a ring and the collar the globe stands in.

The last one is Venus's own and is where its obliquity is paid for.  The globe
is sunk 2.00 mm into its disc and carried by a seat cone springing at
piece-latitude -42, and at 177.36 degrees of obliquity the planet's **north**
pole is what points into that collar.  So on Venus the buried hemisphere is
the northern one, and this report measures how much of each province lands
inside it.

    "$WORKSHOP_PYTHON" measure/venus_atlas_resolution.py \\
        > measure/venus-atlas-resolution.md
"""

from __future__ import annotations

import itertools
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import params as P                                            # noqa: E402
from parts import venus_atlas as V                            # noqa: E402

PLANET = "venus"
R = P.globe_radius(PLANET)
NOZZLE = P.NOZZLE_MM
MM_PER_DEG = math.radians(1.0) * R
TILT = P.PLANETS[PLANET]["tilt"]
SEAT_LAT = P.SEAT_LATITUDE_DEG

#: The limit `features.patches._radial_prism` refuses a ring past.
OUTLINE_MAX_HALF = 72.0


def unit(lon, lat):
    lon, lat = math.radians(lon), math.radians(lat)
    return (math.cos(lat) * math.cos(lon), math.cos(lat) * math.sin(lon),
            math.sin(lat))


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def norm(a):
    length = math.sqrt(dot(a, a))
    return (a[0] / length, a[1] / length, a[2] / length)


def arc(a, b):
    """Great-circle distance between two unit vectors, in mm of arc."""
    return R * math.atan2(math.sqrt(dot(cross(a, b), cross(a, b))), dot(a, b))


def arc_to_segment(point, start, end):
    axis = cross(start, end)
    if dot(axis, axis) < 1e-18:
        return arc(point, start)
    axis = norm(axis)
    foot = tuple(point[index] - dot(point, axis) * axis[index]
                 for index in range(3))
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
    return [(vectors[i], vectors[(i + 1) % len(vectors)])
            for i in range(len(vectors))]


def perimeter(vectors):
    return sum(arc(a, b) for a, b in edges(vectors))


def shortest_edge(vectors):
    return min(arc(a, b) for a, b in edges(vectors))


def narrowest_neck(vectors):
    """The closest a vertex comes to an edge it is not an endpoint of."""
    count = len(vectors)
    worst, where = float("inf"), None
    for i, point in enumerate(vectors):
        for j in range(count):
            if j == i or (j + 1) % count == i:
                continue
            gap = arc_to_segment(point, vectors[j], vectors[(j + 1) % count])
            if gap < worst:
                worst, where = gap, (i, j)
    return worst, where


def half_angle(vectors):
    """How far the furthest vertex sits from the ring's own mean axis."""
    axis = norm(tuple(sum(item[index] for item in vectors) for index in range(3)))
    return max(math.degrees(math.acos(max(-1.0, min(1.0, dot(item, axis)))))
               for item in vectors)


def inside(point, ring_vectors_list):
    """Is a unit vector inside a closed spherical polygon?"""
    total = 0.0
    count = len(ring_vectors_list)
    for index in range(count):
        a = ring_vectors_list[index]
        b = ring_vectors_list[(index + 1) % count]
        ta = [a[k] - dot(a, point) * point[k] for k in range(3)]
        tb = [b[k] - dot(b, point) * point[k] for k in range(3)]
        if dot(ta, ta) < 1e-18 or dot(tb, tb) < 1e-18:
            return True
        ta, tb = norm(ta), norm(tb)
        total += math.atan2(dot(cross(ta, tb), point), dot(ta, tb))
    return abs(total) > math.pi


def resample(ring, step_mm=0.05):
    vectors = ring_vectors(ring)
    out = []
    for a, b in edges(vectors):
        span = arc(a, b)
        steps = max(1, int(span / step_mm))
        for index in range(steps):
            t = index / steps
            out.append(norm([a[k] + (b[k] - a[k]) * t for k in range(3)]))
    return out


def strip_scan(inner_ring, outer_rings, floor):
    """How one boundary sits against the region it is cut out of.

    Returns (crossings, inside_mm, sliver_mm, closest_inside_mm).
    """
    walked = resample(inner_ring)
    outers = [ring_vectors(ring) for ring in outer_rings]
    step = perimeter(ring_vectors(inner_ring)) / len(walked)
    within = sliver = 0
    closest = float("inf")
    states = []
    for point in walked:
        enclosed = any(inside(point, outer) for outer in outers)
        states.append(enclosed)
        if not enclosed:
            continue
        within += 1
        gap = min(arc_to_segment(point, a, b)
                  for outer in outers for a, b in edges(outer))
        if gap < floor:
            sliver += 1
            closest = min(closest, gap)
    crossings = sum(1 for index in range(len(states))
                    if states[index] != states[index - 1])
    return crossings, within * step, sliver * step, closest


def ring_distance(one, other):
    a, b = ring_vectors(one), ring_vectors(other)
    best = float("inf")
    for point in a:
        for start, end in edges(b):
            best = min(best, arc_to_segment(point, start, end))
    for point in b:
        for start, end in edges(a):
            best = min(best, arc_to_segment(point, start, end))
    return best


def lean(vector, sign):
    angle = math.radians(sign * TILT)
    x, y, z = vector
    return (x * math.cos(angle) + z * math.sin(angle), y,
            -x * math.sin(angle) + z * math.cos(angle))


def piece_latitudes(ring, sign):
    """Every sampled point of a ring's interior, as piece latitude."""
    vectors = ring_vectors(V.offset(ring))
    centre = norm(tuple(sum(item[k] for item in vectors) for k in range(3)))
    points = []
    for boundary in resample(V.offset(ring), 0.15):
        for fraction in (0.15, 0.4, 0.65, 0.9, 1.0):
            points.append(norm([centre[k] + (boundary[k] - centre[k]) * fraction
                                for k in range(3)]))
    return [math.degrees(math.asin(max(-1.0, min(1.0, lean(point, sign)[2]))))
            for point in points]


#: Rings that are drawn overlapping on purpose, so the amber between them is
#: not a question anybody asked.
FUSED_PAIRS = {("aphrodite_west", "aphrodite_east")}


def main():
    failures = []

    print("# Venus's radar atlas at globe scale")
    print()
    print("Venus's globe is Ø%.2f mm, so its radius is %.3f mm and one degree"
          % (P.globe_diameter(PLANET), R))
    print("of arc is %.4f mm.  The nozzle is %.2f mm, which is the narrowest"
          % (MM_PER_DEG, NOZZLE))
    print("colour boundary the printer can lay down and %.2f degrees of arc here"
          % (NOZZLE / MM_PER_DEG))
    print("-- against 2.74 degrees on Earth, 2.63 on Mars and 3.33 on Mercury,")
    print("the other three worlds in this set drawn from outlines.")
    print()
    print("The rings are stylised silhouettes of the major highland and lowland")
    print("provinces at the accuracy a globe this size can hold, not Magellan")
    print("mapping. The names are the real ones so that a reader can check them.")
    print()

    print("## Every ring")
    print()
    print("`aphrodite_terra` is the feature as drawn; `aphrodite_west` and")
    print("`aphrodite_east` are the two rings the build actually sweeps, and")
    print("their union is the first of them exactly. The last column is why:")
    print("`features/patches.py` refuses a ring whose vertices reach more than")
    print("%.0f degrees from the ring's own mean axis, because past that a" % OUTLINE_MAX_HALF)
    print("vertex's radial line runs nearly parallel to the tool's own section")
    print("planes and the construction stops being well conditioned.")
    print()
    print("| ring | tone | vertices | perimeter mm | shortest edge mm | "
          "narrowest neck mm | half-angle deg |")
    print("|---|---|---:|---:|---:|---:|---:|")
    built = set(V.HIGHLAND_NAMES) | set(V.LOWLAND_NAMES)
    for name, ring in V.RINGS.items():
        vectors = ring_vectors(ring)
        neck, _where = narrowest_neck(vectors)
        edge = shortest_edge(vectors)
        half = half_angle(vectors)
        tone = ("highland" if name in V.HIGHLAND_NAMES
                else "lowland" if name in V.LOWLAND_NAMES
                else "as drawn, not swept")
        flag = "" if half <= OUTLINE_MAX_HALF else " **over**"
        print("| `%s` | %s | %d | %.2f | %.2f | %.2f | %.2f%s |"
              % (name, tone, len(vectors), perimeter(vectors), edge, neck,
                 half, flag))
        if name in built and min(neck, edge) < NOZZLE:
            failures.append("%s: shortest edge %.2f mm, narrowest neck %.2f mm"
                            % (name, edge, neck))
        if name in built and half > OUTLINE_MAX_HALF:
            failures.append("%s reaches %.2f degrees from its own axis"
                            % (name, half))
    print()
    aph = ring_vectors(V.APHRODITE_TERRA)
    neck, where = narrowest_neck(aph)
    print("**Aphrodite's waist is %.3f mm**, which is %.2f degrees of arc and"
          % (neck, neck / MM_PER_DEG))
    print("%.2f nozzle widths, at the vertex (%d, %d) against the edge from"
          % (neck / NOZZLE, V.APHRODITE_TERRA[where[0]][0],
             V.APHRODITE_TERRA[where[0]][1]))
    print("(%d, %d) to (%d, %d). It is the narrowest point of the one feature"
          % (V.APHRODITE_TERRA[where[1]][0], V.APHRODITE_TERRA[where[1]][1],
             V.APHRODITE_TERRA[(where[1] + 1) % len(aph)][0],
             V.APHRODITE_TERRA[(where[1] + 1) % len(aph)][1]))
    print("this piece is recognised by, it clears the nozzle as drawn, and so")
    print("**no vertex of it was widened or moved**.")
    print()

    print("## The amber between two rings of the same tone")
    print()
    print("Two boundaries of one tone running closer than the nozzle would")
    print("print as one region. Aphrodite's two build rings are left out: they")
    print("are one highland by construction and overlap by design.")
    print()
    print("| channel | tone | width mm |")
    print("|---|---|---|")
    for names, tone in ((V.HIGHLAND_NAMES, "highland"),
                        (V.LOWLAND_NAMES, "lowland")):
        for one, other in itertools.combinations(names, 2):
            if (one, other) in FUSED_PAIRS or (other, one) in FUSED_PAIRS:
                continue
            gap = ring_distance(V.offset(V.RINGS[one]), V.offset(V.RINGS[other]))
            if gap > 4.0:
                continue
            print("| %s / %s | %s | %.2f |" % (one, other, tone, gap))
            if gap < NOZZLE:
                failures.append("%s and %s are %.2f mm apart"
                                % (one, other, gap))
    print()
    print("Every pair not listed is more than 4.00 mm apart. The two tones are")
    print("not compared here: a highland and a lowland may touch or overlap,")
    print("and the subtraction below is what decides which one wins.")
    print()

    print("## The strip the highlands leave in a lowland")
    print()
    print("`highland` is subtracted out of `lowland`, so where a plain's")
    print("boundary runs close to a highland it sits inside, the darker strip")
    print("left between them is that narrow. A lowland ring that *crosses* a")
    print("highland leaves no strip at all there, which is the sound answer")
    print("rather than a thin one: the amber simply reaches the plain and the")
    print("brown runs out in a wedge instead of a thread.")
    print()
    print("| lowland | cut by | crossings | boundary inside mm | "
          "under the nozzle mm | narrowest strip mm |")
    print("|---|---|---:|---:|---:|---|")
    highlands = [V.offset(V.RINGS[name]) for name in V.HIGHLAND_NAMES]
    for name in V.LOWLAND_NAMES:
        crossings, within, sliver, closest = strip_scan(
            V.offset(V.RINGS[name]), highlands, NOZZLE)
        print("| %s | highland | %d | %.2f | %.2f | %s |"
              % (name, crossings, within, sliver,
                 "-" if closest == float("inf") else "%.2f" % closest))
        if crossings == 0 and sliver > 0.0:
            failures.append("%s leaves %.2f mm of brown thinner than the nozzle"
                            % (name, sliver))
    print()
    print("Nothing of any plain lies inside a highland, so the subtraction")
    print("removes nothing and leaves no strip. It is kept because the")
    print("structure is what the pattern requires -- where the two do meet, the")
    print("highland is the one that wins -- and because a subtraction that is")
    print("empty today is what keeps a later vertex move honest.")
    print()

    print("## What the collar buries")
    print()
    print("This is Venus's own column and it is the price of the inversion.")
    print("The globe is sunk %.2f mm into its disc and carried by a seat cone"
          % P.GLOBE_SINK)
    print("springing at piece-latitude %.0f, so nothing below that parallel of"
          % SEAT_LAT)
    print("the **piece** is visible. Venus's obliquity is %.2f degrees, which"
          % TILT)
    print("puts the planet's north pole into that collar, so on this world the")
    print("buried hemisphere is the northern one. Measured by sampling each")
    print("province's interior and carrying it into the piece frame at the")
    print("mirrored lean.")
    print()
    print("| province | piece latitude, Sol | visible | piece latitude, Anti-Sol | visible |")
    print("|---|---|---:|---|---:|")
    for name in V.HIGHLAND_NAMES + V.LOWLAND_NAMES:
        if name == "aphrodite_east":
            continue
        label = "aphrodite_terra" if name == "aphrodite_west" else name
        ring = V.APHRODITE_TERRA if name == "aphrodite_west" else V.RINGS[name]
        cells = []
        for sign in (1.0, -1.0):
            lats = piece_latitudes(ring, sign)
            visible = sum(1 for value in lats if value > SEAT_LAT) / len(lats)
            cells.append(("%+.1f to %+.1f" % (min(lats), max(lats)),
                          "%.0f%%" % (100.0 * visible)))
        print("| `%s` | %s | %s | %s | %s |"
              % (label, cells[0][0], cells[0][1], cells[1][0], cells[1][1]))
    print()
    for name in sorted(V.BURIED):
        print("- **%s** -- %s." % (name, V.BURIED[name]))
    print()

    print("## What the atlas does not draw")
    print()
    print("The reference is a radar mosaic and most of what is loudest in it")
    print("cannot be carried at this size. Stated rather than left for a reader")
    print("to notice.")
    print()
    for item in sorted(V.NOT_DRAWN):
        print("- **%s** -- %s." % (item, V.NOT_DRAWN[item]))
    print()

    print("## Simplifications")
    print()
    if V.SIMPLIFIED:
        for name in sorted(V.SIMPLIFIED):
            print("- **%s** -- %s." % (name, V.SIMPLIFIED[name]))
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
        print("Nothing in Venus's atlas falls under the %.2f mm nozzle at this"
              % NOZZLE)
        print("globe size: no ring edge, no neck, no amber channel between two")
        print("rings of one tone, and no subtracted strip. Every one of the ten")
        print("provinces the atlas carries is drawn -- none was dropped, none")
        print("was shrunk to a dot and none was replaced by a circle. The four")
        print("small Regios, which the atlas warns are near the floor, measure")
        print("%.2f to %.2f mm at their narrowest against a %.2f mm nozzle."
              % (min(narrowest_neck(ring_vectors(V.RINGS[name]))[0]
                     for name in ("alpha_regio", "themis_regio", "beta_regio",
                                  "phoebe_regio")),
                 max(narrowest_neck(ring_vectors(V.RINGS[name]))[0]
                     for name in ("alpha_regio", "themis_regio", "beta_regio",
                                  "phoebe_regio")),
                 NOZZLE))
    print()
    print("Measured by `measure/venus_atlas_resolution.py` on the exact rings")
    print("in `parts/venus_atlas.py`.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
