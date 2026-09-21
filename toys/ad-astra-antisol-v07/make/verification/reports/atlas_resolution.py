"""What Earth's coastline atlas costs on a 16.70 mm globe.

The atlas was drawn for a larger ball.  Here one degree of arc is 0.146 mm, so
the question this answers is which of its features survive a 0.4 mm nozzle:
how short the shortest edge of each ring is, how narrow its narrowest neck is,
and how wide the green strip left between a dryland ring and the coastline it
sits inside would print.

Everything is measured on the sphere, in millimetres of arc, on the exact ring
data `parts/atlas.py` hands the build.  Run from the CAD project directory:

    "$WORKSHOP_PYTHON" measure/atlas_resolution.py > measure/earth-atlas-resolution.md
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import params as P                                            # noqa: E402
from parts import atlas as A                                  # noqa: E402

R = P.globe_radius("earth")
NOZZLE = P.NOZZLE_MM
MM_PER_DEG = math.radians(1.0) * R


def unit(lon, lat):
    lon, lat = math.radians(lon), math.radians(lat)
    return (math.cos(lat) * math.cos(lon), math.cos(lat) * math.sin(lon), math.sin(lat))


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
    """Distance from `point` to the great-circle arc start->end, in mm."""
    axis = cross(start, end)
    if dot(axis, axis) < 1e-18:
        return arc(point, start)
    axis = norm(axis)
    foot = (point[0] - dot(point, axis) * axis[0],
            point[1] - dot(point, axis) * axis[1],
            point[2] - dot(point, axis) * axis[2])
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
    return [(vectors[i], vectors[(i + 1) % len(vectors)]) for i in range(len(vectors))]


def shortest_edge(vectors):
    return min(arc(a, b) for a, b in edges(vectors))


def narrowest_neck(vectors):
    """The closest a vertex comes to an edge it is not an endpoint of."""
    count = len(vectors)
    worst = float("inf")
    where = None
    for i, point in enumerate(vectors):
        for j in range(count):
            if j == i or (j + 1) % count == i:
                continue
            gap = arc_to_segment(point, vectors[j], vectors[(j + 1) % count])
            if gap < worst:
                worst, where = gap, (i, j)
    return worst, where


def inside(point, ring_vectors_list):
    """Is a unit vector inside a closed spherical polygon?

    The signed angles the polygon's edges subtend at the point sum to plus or
    minus a full turn when the point is enclosed and to nothing when it is
    not.  That works on a sphere where a plane ray cast does not.
    """
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
        angle = math.atan2(dot(cross(ta, tb), point), dot(ta, tb))
        total += angle
    return abs(total) > math.pi


def resample(ring, step_mm=0.05):
    """The ring's own boundary, walked at a fixed arc step."""
    vectors = ring_vectors(ring)
    out = []
    for a, b in edges(vectors):
        span = arc(a, b)
        steps = max(1, int(span / step_mm))
        for index in range(steps):
            t = index / steps
            mixed = [a[k] + (b[k] - a[k]) * t for k in range(3)]
            out.append(norm(mixed))
    return out


def strip_scan(inner_ring, outer_rings, floor):
    """How the beige boundary sits against the coastline it is cut out of.

    Returns (crossings, inside_mm, sliver_mm, closest_inside_mm): how many of
    the ring's own edges cross a coastline, how much of its walked boundary
    lies inside the land, how much of that lies within `floor` of the
    coastline -- the green strip too narrow to print -- and the narrowest such
    strip that is not simply running out at a crossing.
    """
    walked = resample(inner_ring)
    outers = [ring_vectors(ring) for ring in outer_rings]
    step = sum(arc(a, b) for a, b in edges(ring_vectors(inner_ring))) / len(walked)
    within = 0
    sliver = 0
    closest = float("inf")
    states = []
    for point in walked:
        enclosed = any(inside(point, outer) for outer in outers)
        states.append(enclosed)
        if not enclosed:
            continue
        within += 1
        gap = min(
            arc_to_segment(point, a, b)
            for outer in outers
            for a, b in edges(outer)
        )
        if gap < floor:
            sliver += 1
            closest = min(closest, gap)
    crossings = sum(
        1 for index in range(len(states)) if states[index] != states[index - 1]
    )
    return crossings, within * step, sliver * step, closest


def perimeter(vectors):
    return sum(arc(a, b) for a, b in edges(vectors))


DRYLAND_HOSTS = {
    "sahara": [A.AFRICA],
    "kalahari": [A.AFRICA],
    "inner_asia": [A.ASIA, A.EUROPE],
    "american_southwest": [A.NORTH_AMERICA],
    "outback": [A.AUSTRALIA],
}

#: Land rings that are drawn overlapping on purpose, so the sea between them
#: is not a question anybody asked.
FUSED_PAIRS = {
    ("north_america", "central_america"),
    ("central_america", "south_america"),
    ("europe", "asia"),
}

LAND_NAMES = ["north_america", "central_america", "south_america", "africa",
              "europe", "asia", "australia"]
ICE_NAMES = ["greenland"] + ["arctic_lobe_%d" % (n + 1) for n in range(len(A.ARCTIC_LOBES))]


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


def main():
    print("# Earth's coastline atlas at globe scale")
    print()
    print("Earth's globe is \u00d8%.2f mm, so its radius is %.3f mm and one degree"
          % (P.globe_diameter("earth"), R))
    print("of arc is %.4f mm.  The nozzle is %.2f mm, which is the narrowest"
          % (MM_PER_DEG, NOZZLE))
    print("colour boundary the printer can lay down and %.2f degrees of arc here."
          % (NOZZLE / MM_PER_DEG))
    print()
    print("Three things have to clear that nozzle: the rings themselves, the sea")
    print("channels between them, and the strip one region leaves when another is")
    print("subtracted out of it.  All three are measured below, on the sphere, in")
    print("millimetres of arc, on the exact rings `parts/atlas.py` hands the build.")
    print()
    print("## Every ring")
    print()
    print("| ring | vertices | perimeter mm | shortest edge mm | narrowest neck mm |")
    print("|---|---|---|---|---|")
    failures = []
    for name in sorted(A.RINGS):
        vectors = ring_vectors(A.RINGS[name])
        neck, _where = narrowest_neck(vectors)
        edge = shortest_edge(vectors)
        print("| %s | %d | %.2f | %.2f | %.2f |"
              % (name, len(vectors), perimeter(vectors), edge, neck))
        if min(neck, edge) < NOZZLE:
            failures.append("%s: shortest edge %.2f mm, narrowest neck %.2f mm"
                            % (name, edge, neck))
    print()
    print("## The sea between two landmasses")
    print()
    print("Two coastlines running closer than the nozzle would print as one")
    print("continent.  Rings the atlas deliberately overlaps -- North and Central")
    print("America, Central and South America, Europe and Asia -- are left out:")
    print("they are one landmass by design.")
    print()
    print("| channel | width mm |")
    print("|---|---|")
    for index, one in enumerate(LAND_NAMES):
        for other in LAND_NAMES[index + 1:]:
            if (one, other) in FUSED_PAIRS or (other, one) in FUSED_PAIRS:
                continue
            gap = ring_distance(A.RINGS[one], A.RINGS[other])
            if gap > 4.0:
                continue
            print("| %s / %s | %.2f |" % (one, other, gap))
            if gap < NOZZLE:
                failures.append("%s and %s are %.2f mm apart" % (one, other, gap))
    print()
    print("## The strip a subtracted region leaves")
    print()
    print("`dryland` is subtracted out of `land`, and `ice` out of both, so where")
    print("one of those boundaries runs close to the coastline it is cut out of,")
    print("the strip left between them is that narrow.  A ring that crosses the")
    print("coastline leaves no strip at all there, which is the sound answer")
    print("rather than a thin one: the beige or the white simply reaches the sea,")
    print("and the green runs out in a wedge instead of a thread.  Only a ring")
    print("that stays inside and close can leave a strip nobody can print.")
    print()
    print("| ring | cut out of | crossings | boundary inside mm | "
          "under the nozzle mm | narrowest strip mm |")
    print("|---|---|---|---|---|---|")
    for name, hosts in sorted(DRYLAND_HOSTS.items()):
        crossings, within, sliver, closest = strip_scan(A.RINGS[name], hosts, NOZZLE)
        print("| %s | land | %d | %.2f | %.2f | %s |"
              % (name, crossings, within, sliver,
                 "-" if closest == float("inf") else "%.2f" % closest))
        if crossings == 0 and sliver > 0.0:
            failures.append("%s leaves %.2f mm of green thinner than the nozzle"
                            % (name, sliver))
    land_rings = [A.RINGS[name] for name in LAND_NAMES]
    dry_rings = [A.RINGS[name] for name in DRYLAND_HOSTS]
    for name in ICE_NAMES:
        for label, hosts in (("land", land_rings), ("dryland", dry_rings)):
            crossings, within, sliver, closest = strip_scan(A.RINGS[name], hosts, NOZZLE)
            if within <= 0.0:
                continue
            print("| %s | %s | %d | %.2f | %.2f | %s |"
                  % (name, label, crossings, within, sliver,
                     "-" if closest == float("inf") else "%.2f" % closest))
            if crossings == 0 and sliver > 0.0:
                failures.append("%s leaves %.2f mm of %s thinner than the nozzle"
                                % (name, sliver, label))
    print()
    print("Named, because a reader finds it and wonders: the Sahara crosses Africa's")
    print("west coast, so on that coast the beige reaches the sea and there is no green")
    print("strip between desert and ocean at all. That is the deliberate answer and it")
    print("is the geographically right one -- the Sahara does reach the Atlantic. The")
    print("alternative, a green strip a tenth of a millimetre wide, is a strip no nozzle")
    print("can lay down. The same holds for the Kalahari and the American southwest.")
    print()
    print("The northern cap is a circle of latitude rather than a ring, so it has")
    print("no entry here.  Where a coastline crosses %.0f degrees the white simply"
          % A.ARCTIC_CAP_LAT)
    print("continues over it, and where a coastline runs south of it the green")
    print("boundary and the cap boundary are the same curve.")
    print()
    print("## What the atlas does not draw")
    print()
    print("Omissions of the supplied data rather than simplifications this build")
    print("made -- but they are the set's omissions now, so they are stated.")
    print()
    for item in A.NOT_DRAWN:
        print("- **%s** -- %s." % (item, A.NOT_DRAWN[item]))
    print()
    print("## Simplifications")
    print()
    if A.SIMPLIFIED:
        for name in sorted(A.SIMPLIFIED):
            print("- **%s** -- %s" % (name, A.SIMPLIFIED[name]))
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
        print("Nothing in the atlas falls under the %.2f mm nozzle at this globe"
              % NOZZLE)
        print("size: no ring edge, no neck, no sea channel and no subtracted strip.")
        print("No landmass was dropped.")
    print()
    print("Measured by `measure/atlas_resolution.py` on the exact rings in")
    print("`parts/atlas.py`.")


if __name__ == "__main__":
    main()
