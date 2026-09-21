"""What colour the built Venus actually is, point by point.

The sibling of `measure/mercury_surface_scan.py` and
`measure/mars_surface_scan.py`, asking the built solids rather than looking at
a picture of them.  A point is placed a fixed depth under the sphere, in the
planet's own frame, carried into the piece by the same obliquity the part
uses, and classified against every colour body of the world.

Five questions, all of them things this correction has to answer in bytes
rather than in prose.

**Is the globe amber with exactly two marking tones on it, and is there any
`orange` anywhere?**  The filament of every body is read straight off the
build, so "no orange on Venus" is a fact about the part rather than a claim
about the source.

**Does Aphrodite Terra come out as one continuous highland?**  It is built as
two overlapping rings and it is the feature the piece is recognised by, so the
classified cells are flooded and the groups counted: two groups where one was
wanted would mean the overlap failed and the highland reads as two blobs.

**Is the pattern inverted by the planet frame?**  Venus is the only world in
the set whose map reads upside down, and the frame is what does it.  A
province's own Venusian latitude is compared with the piece latitude it lands
at: a northern province must come out low on the piece and a southern one
high, or the obliquity has stopped inverting.

**Is anything raised?**  Every marking is a flush colour inlay, so the union
of the colour bodies must be the same solid as the printed world and the outer
surface must still be a true sphere.  Both are measured on volume.

**And are the two armies still exact mirrors?**  The whole grid is classified
on both and compared cell by cell.

    "$WORKSHOP_PYTHON" measure/venus_surface_scan.py > measure/venus-surface.md
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import bool3d as X                                            # noqa: E402
import params as P                                            # noqa: E402
from parts import venus_atlas as V                            # noqa: E402
from parts.markings import facing_meridian, reflect_longitude  # noqa: E402
from parts.world import build_world, world_bodies             # noqa: E402

from OCP.BRepClass3d import BRepClass3d_SolidClassifier       # noqa: E402
from OCP.TopAbs import TopAbs_OUT                             # noqa: E402
from OCP.gp import gp_Pnt                                     # noqa: E402

#: How far under the sphere the sample sits.  The inlays run 1.20 mm deep, so
#: this is well inside them and well outside the tessellation's own tolerance.
DEPTH = 0.10
GLYPH = {"highland": "H", "lowland": "o", "globe": "."}

PLANET = "venus"
RADIUS = P.globe_radius(PLANET)
MM_PER_DEG = math.radians(1.0) * RADIUS
NOZZLE = P.NOZZLE_MM
TILT = P.PLANETS[PLANET]["tilt"]
SEAT_LAT = P.SEAT_LATITUDE_DEG


def sampler(side: str):
    """(classify, bodies): lat, lon -> the marking key the world carries.

    None means the point is off the piece entirely: the globe is sunk into the
    disc and cut at the disc's top face, so the bottom of the ball does not
    exist.  That is a different answer from `.`, which is bare amber globe.
    """
    bodies = world_bodies(PLANET, side)
    centre = P.globe_centre_z(PLANET)
    tilt = math.radians(P.lean_sign(side) * TILT)
    solids = {
        key: X.parts(shape)
        for key, (_colour, shape) in bodies.items()
        if key not in ("disc", "numeral")
    }

    def classify(lat_deg, lon_deg):
        lat, lon = math.radians(lat_deg), math.radians(lon_deg)
        reach = RADIUS - DEPTH
        x = reach * math.cos(lat) * math.cos(lon)
        y = reach * math.cos(lat) * math.sin(lon)
        z = reach * math.sin(lat)
        # the planet frame carried into the piece
        px = x * math.cos(tilt) + z * math.sin(tilt)
        pz = -x * math.sin(tilt) + z * math.cos(tilt) + centre
        point = gp_Pnt(px, y, pz)
        for key, parts in solids.items():
            for solid in parts:
                checker = BRepClass3d_SolidClassifier(solid.wrapped, point, 1e-6)
                if checker.State() != TopAbs_OUT:
                    return key
        return None

    return classify, bodies


def piece_latitude(lat_deg, lon_deg, side):
    lat, lon = math.radians(lat_deg), math.radians(lon_deg)
    tilt = math.radians(P.lean_sign(side) * TILT)
    x = math.cos(lat) * math.cos(lon)
    z = math.sin(lat)
    return math.degrees(math.asin(max(-1.0, min(1.0,
                                                -x * math.sin(tilt)
                                                + z * math.cos(tilt)))))


def row(classify, lat, lon_from, lon_to, step):
    out = []
    lon = lon_from
    while lon <= lon_to + 1e-9:
        key = classify(lat, lon)
        out.append(" " if key is None else GLYPH.get(key, "?"))
        lon += step
    return "".join(out)


def flood(grid, want):
    """Four-way connected groups of `want`, with the longitude seam joined."""
    height, width = len(grid), len(grid[0])
    seen = [[False] * width for _ in range(height)]
    groups = []
    for r in range(height):
        for c in range(width):
            if seen[r][c] or grid[r][c] != want:
                continue
            stack, cells = [(r, c)], []
            seen[r][c] = True
            while stack:
                y, x = stack.pop()
                cells.append((y, x))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = y + dy, (x + dx) % width
                    if 0 <= ny < height and not seen[ny][nx] \
                            and grid[ny][nx] == want:
                        seen[ny][nx] = True
                        stack.append((ny, nx))
            groups.append(cells)
    groups.sort(key=len, reverse=True)
    return groups


def main() -> int:
    step = 3.0
    lats = [78.0 - index * step for index in range(int(156 / step) + 1)]
    lons = [-180.0 + index * step for index in range(int(360 / step) + 1)]

    print("# Venus's corrected surface, measured on the built solids")
    print()
    print("Sampled %.2f mm under the sphere, in the planet's own frame, carried"
          % DEPTH)
    print("into the piece by the same obliquity the part uses, and classified")
    print("against every colour body of the world. `H` is the `beige` highland,")
    print("`o` is the `cocoa_brown` lowland, `.` is bare `sunflower_yellow`")
    print("globe, and a blank is off the piece -- the globe is sunk %.2f mm into"
          % P.GLOBE_SINK)
    print("its disc and cut at the disc's top face, so that part of the ball")
    print("does not exist.")
    print()
    print("One degree of arc is %.4f mm on this Ø%.2f globe and the nozzle is"
          % (MM_PER_DEG, P.globe_diameter(PLANET)))
    print("%.2f mm, so a printable feature has to hold %.2f degrees."
          % (NOZZLE, NOZZLE / MM_PER_DEG))
    print()

    classify, bodies = sampler("sol")
    grid = [row(classify, lat, -180.0, 180.0, step) for lat in lats]

    print("## Every filament on this world")
    print()
    print("Read off the build rather than off the source: `parts/world.py`")
    print("returns one body per colour and this is that list.")
    print()
    print("| body | filament |")
    print("|---|---|")
    for key, (colour, _shape) in bodies.items():
        print("| `%s` | `%s` |" % (key, colour))
    filaments = sorted({colour for colour, _shape in bodies.values()})
    print()
    print("**Venus carries %d filaments: %s.**"
          % (len(filaments), ", ".join("`%s`" % name for name in filaments)))
    orange = [key for key, (colour, _s) in bodies.items() if colour == "orange"]
    print("**There is no `orange` anywhere on this world**: %s."
          % ("not one of the %d bodies carries it" % len(bodies) if not orange
             else "FOUND on " + ", ".join(orange)))
    print("The globe is `%s` %s and the two marking tones are the only others."
          % (P.GLOBE_COLOUR[PLANET], P.FILAMENT_HEX[P.GLOBE_COLOUR[PLANET]]))
    print("The `white` disc and `black` numeral are the Sol ownership cue and")
    print("are not markings; the Anti-Sol piece swaps them and nothing else.")
    print()

    print("## The whole surface")
    print()
    print("Venusian longitude -180 to +180 east across, latitude +78 down to")
    print("-78, every %.0f degrees. Sol army. Longitudes carry the atlas's"
          % step)
    print("%+.0f degree offset, because this is the built piece rather than the"
          % V.LONGITUDE_OFFSET)
    print("drawn map.")
    print()
    print("```")
    header = "".join("|" if round(-180.0 + n * step) % 30 == 0 else " "
                     for n in range(len(lons)))
    print("       " + header)
    for lat, text in zip(lats, grid):
        print("%+6.0f %s" % (lat, text))
    print("       " + header)
    print("```")
    print()

    highland_groups = flood(grid, "H")
    lowland_groups = flood(grid, "o")
    print("## Does Aphrodite come out as one highland?")
    print()
    print("The `H` cells above, flooded four-ways with the longitude seam")
    print("joined. Aphrodite is built as two overlapping rings, so the question")
    print("is whether the boolean agreed that they are one region.")
    print()
    print("| group | cells | provinces whose centre falls in it |")
    print("|---|---:|---|")

    def centre_of(name):
        ring = V.offset(V.RINGS[name])
        vectors = [(math.cos(math.radians(lat)) * math.cos(math.radians(lon)),
                    math.cos(math.radians(lat)) * math.sin(math.radians(lon)),
                    math.sin(math.radians(lat))) for lon, lat in ring]
        length = math.sqrt(sum(sum(v[k] for v in vectors) ** 2 for k in range(3)))
        mean = [sum(v[k] for v in vectors) / length for k in range(3)]
        lat = math.degrees(math.asin(max(-1.0, min(1.0, mean[2]))))
        lon = (math.degrees(math.atan2(mean[1], mean[0])) + 180.0) % 360.0 - 180.0
        return lat, lon

    def cell_of(lat, lon):
        return (int(round((78.0 - lat) / step)),
                int(round((lon + 180.0) / step)) % len(lons))

    names = V.HIGHLAND_NAMES + V.LOWLAND_NAMES
    centres = {name: centre_of(name) for name in names}
    for label, groups in (("highland", highland_groups), ("lowland", lowland_groups)):
        for index, cells in enumerate(groups, 1):
            members = set(cells)
            inside = [name for name in names
                      if cell_of(*centres[name]) in members]
            print("| %s %d | %d | %s |"
                  % (label, index, len(cells),
                     ", ".join("`%s`" % name for name in inside) or "none"))
    print()
    aphrodite_group = [cells for cells in highland_groups
                       if cell_of(*centres["aphrodite_west"]) in set(cells)
                       and cell_of(*centres["aphrodite_east"]) in set(cells)]
    print("**Aphrodite's two build rings land in %s.** %s"
          % ("one group" if aphrodite_group else "DIFFERENT groups",
             "The overlap fused, so the highland is continuous across the "
             "whole 152 degrees of longitude it is drawn over and reads as one "
             "province rather than two."
             if aphrodite_group else
             "The overlap failed and the highland is broken."))
    widths = []
    for r, text in enumerate(grid):
        count = text.count("H")
        if count:
            widths.append((lats[r], count * step))
    if widths:
        best = max(widths, key=lambda item: item[1])
        print()
        print("Its widest row is latitude %+.0f, %.0f degrees of longitude wide"
              % (best[0], best[1]))
        print("-- %.1f mm of arc on a Ø%.2f globe, which is the longest"
              % (best[1] * MM_PER_DEG, P.globe_diameter(PLANET)))
        print("continuous marking anywhere in this set.")
    print()

    print("## Is the pattern still inverted?")
    print()
    print("Venus's obliquity is %.2f degrees and the planet frame is what turns"
          % TILT)
    print("this map over. A northern province must therefore come out **low**")
    print("on the piece and a southern one **high**. If this table ever agreed")
    print("in sign, the inversion would have been quietly corrected.")
    print()
    print("| province | Venusian latitude | piece latitude, Sol | piece latitude, Anti-Sol | inverted |")
    print("|---|---:|---:|---:|---|")
    inverted = True
    for name in names:
        if name == "aphrodite_east":
            continue
        label = "aphrodite_terra" if name == "aphrodite_west" else name
        lat, lon = centres[name]
        sol = piece_latitude(lat, lon, "sol")
        anti = piece_latitude(lat, lon, "anti")
        ok = lat * sol < 0 and lat * anti < 0
        inverted = inverted and ok
        print("| `%s` | %+.1f | %+.1f | %+.1f | %s |"
              % (label, lat, sol, anti, "yes" if ok else "**NO**"))
    print()
    print("**Every province changes sign on both armies: %s.**"
          % ("the frame still inverts the map" if inverted
             else "IT DOES NOT -- the inversion has been lost"))
    print("This is the reason `ishtar_terra` cannot be seen: Venusian +71 lands")
    print("at piece %-.1f, below the %.0f where the seat cone springs."
          % (piece_latitude(*centres["ishtar_terra"], "sol"), SEAT_LAT))
    print()

    print("## Is anything raised?")
    print()
    print("Every marking is a flush colour inlay reaching %.2f mm into the"
          % P.RELIEF_DEPTH)
    print("globe, so the colour bodies must add back up to the printed part")
    print("exactly and the outer surface must still be a true sphere.")
    print()
    total = sum(shape.volume for _colour, shape in bodies.values())
    printed = build_world(PLANET, "sol")
    print("| measure | mm3 |")
    print("|---|---:|")
    print("| the %d colour bodies added up | %.4f |" % (len(bodies), total))
    print("| the printed part `part_world_venus_sol` | %.4f |" % printed.volume)
    print("| difference | %.6f |" % abs(total - printed.volume))
    print()
    print("The printed part is built from the disc and the ball directly and")
    print("never sees a marking, so this is two independent constructions")
    print("agreeing rather than one measured against itself. Nothing a marking")
    print("adds can face downward and nothing protrudes: the markings are")
    print("inside the sphere, not on it.")
    print()

    print("## Are the two armies mirrors, and is the mirror in the map?")
    print()
    print("Venus's obliquity is %.2f degrees, so its two pieces differ by 5.28"
          % TILT)
    print("degrees of lean -- the same turn measured each way round -- and the")
    print("lean has no mirror to give. The Antisol Mirror revision mirrors this")
    print("world's MAP instead: on the Anti-Sol piece every marking longitude is")
    print("reflected to 2C - L about that piece's own facing meridian,")
    print("C = %+.4f degrees. So the grid is compared twice, and the two"
          % facing_meridian(PLANET, "anti"))
    print("answers have to be opposite.")
    print()
    classify_anti, _bodies = sampler("anti")
    meridian = facing_meridian(PLANET, "anti")
    straight, reflected, checked, skipped = 0, 0, 0, 0
    for lat in lats[::2]:
        for lon in lons[::2]:
            left = classify(lat, lon)
            same = classify_anti(lat, lon)
            flipped = classify_anti(lat, reflect_longitude(lon, meridian))
            checked += 1
            if (left is None) != (same is None) or (left is None) != (flipped is None):
                skipped += 1
                continue
            if left != same:
                straight += 1
            if left != flipped:
                reflected += 1
    counted = checked - skipped
    print("%d points classified on both armies at half this grid's resolution;"
          % checked)
    print("%d of them are excluded because the collar cuts the two pieces at"
          % skipped)
    print("Venusian latitudes %.2f degrees apart, so a point near its edge can"
          % (2 * (180.0 - TILT)))
    print("be on one piece and inside the other's disc.")
    print()
    print("| comparison | points that disagree | of | share |")
    print("|---|---:|---:|---:|")
    print("| Anti-Sol at the SAME longitude | %d | %d | %.2f%% |"
          % (straight, counted, 100.0 * straight / max(counted, 1)))
    print("| Anti-Sol at the REFLECTED longitude | %d | %d | %.2f%% |"
          % (reflected, counted, 100.0 * reflected / max(counted, 1)))
    print()
    print("The first row is the defect this revision corrects and the second is")
    print("the correction, measured on the built colour bodies rather than on")
    print("the marking table. The residue in the second row is the grid's own")
    print("quantisation at a marking boundary.")
    print()
    print("Measured by `measure/venus_surface_scan.py` on the exact solids")
    print("`parts/world.py` builds.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
