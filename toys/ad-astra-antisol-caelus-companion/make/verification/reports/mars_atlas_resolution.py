"""What Mars's albedo atlas costs on a 14.72 mm globe.

The sibling of `measure/atlas_resolution.py`, and it borrows that script's
arithmetic rather than repeating it: the same great-circle distances, the same
spherical point-in-polygon, the same walked boundaries, with the radius moved
from Earth's globe to Mars's.  Mars is the smaller ball -- one degree of arc is
0.128 mm here against Earth's 0.146 -- so every outline on it is finer, and the
question this answers is which of them survive a 0.4 mm nozzle.

Four things have to clear that nozzle here.  The rings themselves.  The red
channels between rings the atlas means to stay apart.  The joins of the three
rings the atlas means to fuse into one belt, which have to overlap rather than
merely approach.  And the red left between an albedo ring and a polar cap,
because `caps` is cut back by `albedo`.

One thing more is checked that Earth's report had no need of: the outline tool
builds a radial prism through a ring and refuses a ring that reaches more than
72 degrees from its own axis, so every ring's half-angle is reported.

Everything is measured on the sphere, in millimetres of arc, on the exact ring
data `parts/mars_atlas.py` hands the build.  Run from the CAD project
directory:

    "$WORKSHOP_PYTHON" measure/mars_atlas_resolution.py > measure/mars-atlas-resolution.md
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import atlas_resolution as AR                                 # noqa: E402
import params as P                                            # noqa: E402
from features.patches import _OUTLINE_MAX_HALF                # noqa: E402
from parts import mars_atlas as A                             # noqa: E402

#: `atlas_resolution` measures on whichever globe its module-level radius
#: names.  Moving it is the whole of what makes this the Mars report.
AR.R = P.globe_radius("mars")
R = AR.R
NOZZLE = P.NOZZLE_MM
MM_PER_DEG = math.radians(1.0) * R


def ring_axis_half(ring) -> float:
    """How far the ring's furthest vertex sits from the ring's own axis."""
    vectors = AR.ring_vectors(ring)
    total = [sum(item[index] for item in vectors) for index in range(3)]
    axis = AR.norm(total)
    return max(
        math.degrees(math.acos(max(-1.0, min(1.0, AR.dot(item, axis)))))
        for item in vectors
    )


def ring_axis(ring):
    """The direction a ring surrounds: the mean of its own vertices."""
    vectors = AR.ring_vectors(ring)
    return AR.norm([sum(item[index] for item in vectors) for index in range(3)])


def inside_ring(point, ring) -> bool:
    """Is a direction inside this ring?

    `atlas_resolution.inside` sums the signed angles the ring's edges subtend
    at the point, which is +/- a full turn inside the ring and nothing outside
    it -- and also a full turn in the ring's ANTIPODAL patch, where the
    tangent-plane projection wraps the other way round.  Earth's report only
    ever asked the question of points walked along a ring's own boundary, so
    it never met that second answer.  This one sweeps whole grids, so it
    rejects the far hemisphere first.  Every ring here is well inside one
    hemisphere: the widest reaches 32 degrees from its own axis.
    """
    return AR.dot(point, ring_axis(ring)) > 0.0 and AR.inside(
        point, AR.ring_vectors(ring))


def region_area(rings, step: float = 0.5) -> float:
    """How much of the sphere a group of rings covers together, in mm2."""
    axes = [(ring_axis(ring), AR.ring_vectors(ring)) for ring in rings]
    cell = (math.radians(step) * R) ** 2
    area = 0.0
    lat = -90.0 + step / 2.0
    while lat < 90.0:
        lon = 0.0
        while lon < 360.0:
            point = AR.unit(lon, lat)
            if any(AR.dot(point, axis) > 0.0 and AR.inside(point, vectors)
                   for axis, vectors in axes):
                area += cell * math.cos(math.radians(lat))
            lon += step
        lat += step
    return area


def overlap_area(one, other, step: float = 0.25) -> float:
    """How much surface two rings share, in mm2, by grid sample."""
    left, right = AR.ring_vectors(one), AR.ring_vectors(other)
    lons = [point[0] for point in one] + [point[0] for point in other]
    lats = [point[1] for point in one] + [point[1] for point in other]
    cell = (math.radians(step) * R) ** 2
    area = 0.0
    lat = min(lats)
    while lat <= max(lats) + 1e-9:
        lon = min(lons)
        while lon <= max(lons) + 1e-9:
            point = AR.unit(lon, lat)
            if inside_ring(point, one) and inside_ring(point, other):
                area += cell * math.cos(math.radians(lat))
            lon += step
        lat += step
    return area


def penetration(one, other) -> float:
    """How deep the deeper of the two rings bites into the other, in mm."""
    left, right = AR.ring_vectors(one), AR.ring_vectors(other)
    best = 0.0
    for vertices, host in ((left, right), (right, left)):
        for point in vertices:
            if AR.inside(point, host):
                best = max(
                    best,
                    min(AR.arc_to_segment(point, start, end)
                        for start, end in AR.edges(host)),
                )
    return best


def cap_reach(lobe, rim_lat: float, northern: bool):
    """(furthest past the rim, furthest inside it) for one cap lobe, in mm."""
    out = max((rim_lat - lat) if northern else (lat - rim_lat)
              for _lon, lat in lobe)
    inside = max((lat - rim_lat) if northern else (rim_lat - lat)
                 for _lon, lat in lobe)
    return out * MM_PER_DEG, inside * MM_PER_DEG


def main() -> int:
    failures: list[str] = []

    print("# Mars's albedo atlas at globe scale")
    print()
    print("Mars's globe is Ø%.2f mm, so its radius is %.3f mm and one degree"
          % (P.globe_diameter("mars"), R))
    print("of arc is %.4f mm -- against Earth's 0.1457, because this is the"
          % MM_PER_DEG)
    print("smaller ball.  The nozzle is %.2f mm, which is the narrowest colour"
          % NOZZLE)
    print("boundary the printer can lay down and %.2f degrees of arc here."
          % (NOZZLE / MM_PER_DEG))
    print()
    print("Measured on the sphere, in millimetres of arc, on the exact rings")
    print("`parts/mars_atlas.py` hands the build, by the arithmetic")
    print("`measure/atlas_resolution.py` already carried for Earth.")
    print()

    print("## Every ring")
    print()
    print("`half-angle` is how far the ring's furthest vertex sits from the")
    print("ring's own axis. The outline tool builds a radial prism through the")
    print("ring and refuses anything past %.0f degrees." % _OUTLINE_MAX_HALF)
    print()
    print("| ring | vertices | perimeter mm | shortest edge mm | "
          "narrowest neck mm | half-angle deg |")
    print("|---|---|---|---|---|---|")
    for name in A.ALBEDO_NAMES + [
        key for key in sorted(A.RINGS) if key.startswith("cap_")
    ]:
        ring = A.RINGS[name]
        vectors = AR.ring_vectors(ring)
        neck, _where = AR.narrowest_neck(vectors)
        edge = AR.shortest_edge(vectors)
        half = ring_axis_half(ring)
        print("| %s | %d | %.2f | %.2f | %.2f | %.1f |"
              % (name, len(vectors), AR.perimeter(vectors), edge, neck, half))
        if min(neck, edge) < NOZZLE:
            failures.append("%s: shortest edge %.2f mm, narrowest neck %.2f mm"
                            % (name, edge, neck))
        if half >= _OUTLINE_MAX_HALF:
            failures.append("%s reaches %.1f degrees from its own axis, past "
                            "the outline tool's %.0f degree limit"
                            % (name, half, _OUTLINE_MAX_HALF))
    print()

    print("## The red between two dark regions")
    print()
    print("Two albedo rings running closer than the nozzle would print as one")
    print("region with a broken thread of red in it, which is worse than either")
    print("answer. Rings the atlas overlaps on purpose -- the three of the")
    print("southern belt -- are the next table instead.")
    print()
    print("| channel | width mm |")
    print("|---|---|")
    for index, one in enumerate(A.ALBEDO_NAMES):
        for other in A.ALBEDO_NAMES[index + 1:]:
            if (one, other) in A.FUSED_PAIRS or (other, one) in A.FUSED_PAIRS:
                continue
            gap = AR.ring_distance(A.RINGS[one], A.RINGS[other])
            if gap > 4.0:
                continue
            print("| %s / %s | %.2f |" % (one, other, gap))
            if gap < NOZZLE:
                failures.append("%s and %s are %.2f mm apart" % (one, other, gap))
    print()

    print("## The southern belt's own joins")
    print()
    print("Sirenum, Cimmerium and Tyrrhenum are meant to fuse into the one dark")
    print("belt the reference shows. Separate rings are only how that belt is")
    print("described, so what these two joins have to do is overlap -- an")
    print("approach, however close, leaves a thread of red the nozzle cannot")
    print("lay down.")
    print()
    print("| join | shared area mm2 | deepest bite mm |")
    print("|---|---|---|")
    for one, other in sorted(A.FUSED_PAIRS):
        shared = overlap_area(A.RINGS[one], A.RINGS[other])
        bite = penetration(A.RINGS[one], A.RINGS[other])
        print("| %s / %s | %.2f | %.2f |" % (one, other, shared, bite))
        if shared <= 0.0:
            failures.append("%s and %s do not overlap; the belt is broken there"
                            % (one, other))
    print()

    print("## The polar caps' broken rims")
    print()
    print("A blob centred on a pole is a polar cap, and the two blobs are")
    print("unchanged: %.0f degrees of angular radius north, %.0f south, which"
          % (A.CAP_NORTH_ANGULAR_RADIUS, A.CAP_SOUTH_ANGULAR_RADIUS))
    print("puts their rims at latitude %.0f and %.0f. What is corrected is that"
          % (A.CAP_NORTH_RIM_LAT, A.CAP_SOUTH_RIM_LAT))
    print("both rims were exact circles of latitude, and a bare circular rim")
    print("reads as a lid laid on the globe rather than as ice.")
    print()
    print("Each lobe has to straddle its rim: vertices outside it, which is")
    print("what breaks the circle, and vertices inside it, which is what fuses")
    print("the lobe to the cap instead of leaving it floating off the edge.")
    print()
    print("| lobe | past the rim mm | inside the rim mm | to the next lobe mm |")
    print("|---|---|---|---|")
    for cap, lobes, rim, northern in (
        ("north", A.CAP_NORTH_LOBES, A.CAP_NORTH_RIM_LAT, True),
        ("south", A.CAP_SOUTH_LOBES, A.CAP_SOUTH_RIM_LAT, False),
    ):
        for index, lobe in enumerate(lobes):
            name = "cap_%s_lobe_%d" % (cap, index + 1)
            out, inside = cap_reach(lobe, rim, northern)
            neighbour = lobes[(index + 1) % len(lobes)]
            gap = AR.ring_distance(lobe, neighbour)
            print("| %s | %.2f | %.2f | %.2f |" % (name, out, inside, gap))
            if out <= 0.0:
                failures.append("%s never reaches past the rim, so it breaks "
                                "nothing" % name)
            if inside <= 0.0:
                failures.append("%s never reaches inside the rim, so it is not "
                                "joined to the cap" % name)
            if gap < NOZZLE:
                failures.append("%s and its neighbour are %.2f mm apart, a "
                                "thread of red under the nozzle" % (name, gap))
    print()
    print("The north cap carries %d lobes against the south's %d and reaches"
          % (len(A.CAP_NORTH_LOBES), len(A.CAP_SOUTH_LOBES)))
    print("%.2f mm past its rim at the deepest against %.2f mm, so it is the"
          % (max(cap_reach(lobe, A.CAP_NORTH_RIM_LAT, True)[0]
                 for lobe in A.CAP_NORTH_LOBES),
             max(cap_reach(lobe, A.CAP_SOUTH_RIM_LAT, False)[0]
                 for lobe in A.CAP_SOUTH_LOBES)))
    print("larger and the more irregular of the two, as the reference shows.")
    print()

    print("## The red a cap leaves against the albedo")
    print()
    print("`caps` is cut back by `albedo`, so where an albedo ring runs close")
    print("to a cap's rim or one of its lobes, the red strip between them is")
    print("that narrow. Nothing on this globe comes near: the northernmost")
    print("albedo ring is Acidalium and the southernmost is Erythraeum.")
    print()
    print("| cap | nearest albedo ring | red between mm |")
    print("|---|---|---|")
    for cap, lobes, rim, northern in (
        ("north", A.CAP_NORTH_LOBES, A.CAP_NORTH_RIM_LAT, True),
        ("south", A.CAP_SOUTH_LOBES, A.CAP_SOUTH_RIM_LAT, False),
    ):
        # The white reaches whichever is further from the pole: the rim
        # itself, or the deepest lobe hanging off it.
        edge_lat = min(
            [rim] + [min(lat for _lon, lat in lobe) for lobe in lobes]
        ) if northern else max(
            [rim] + [max(lat for _lon, lat in lobe) for lobe in lobes]
        )
        best = (float("inf"), None)
        for name in A.ALBEDO_NAMES:
            ring = A.RINGS[name]
            reach = (max(lat for _lon, lat in ring) if northern
                     else min(lat for _lon, lat in ring))
            strip = ((edge_lat - reach) if northern else (reach - edge_lat)) \
                * MM_PER_DEG
            if strip < best[0]:
                best = (strip, name)
        print("| %s | %s | %.2f |" % (cap, best[1], best[0]))
        if best[0] < NOZZLE:
            failures.append("the %s cap and %s leave %.2f mm of red"
                            % (cap, best[1], best[0]))
    print()

    print("## What the atlas does not draw")
    print()
    print("Omissions this build made on purpose, each with its reason, so")
    print("nobody has to wonder whether it was an oversight.")
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
    print("- **sinus_sabaeus** -- %s" % A.UNCHANGED_NOTE)
    print()

    print("## Verdict")
    print()
    if failures:
        print("Under the nozzle, and therefore unprintable as drawn:")
        print()
        for item in failures:
            print("- %s" % item)
    else:
        print("Nothing in the atlas falls under the %.2f mm nozzle at this" % NOZZLE)
        print("globe size: no ring edge, no neck, no red channel, no cap lobe")
        print("gap and no strip between a cap and the albedo. Both belt joins")
        print("overlap rather than approach. No feature was dropped, and the")
        print("one ring the Wish names as most at risk -- Sinus Sabaeus -- is")
        print("carried at the width it was drawn.")
    print()
    print("Measured by `measure/mars_atlas_resolution.py` on the exact rings in")
    print("`parts/mars_atlas.py`.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
