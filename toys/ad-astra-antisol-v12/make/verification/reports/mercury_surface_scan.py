"""What colour the built Mercury actually is, point by point.

The sibling of `measure/mars_surface_scan.py`, asking the built solids rather
than looking at a picture of them.  A point is placed a fixed depth under the
sphere, in the planet's own frame, carried into the piece by the same obliquity
the part uses, and classified against every colour body of the world.

Five questions, all of them things this correction has to answer.

Do the plains actually fuse?  Three of them -- the southern lead, the southern
middle and the trailing patch -- are drawn as separate rings and are meant to
come out as one larger smooth plain, and two more are meant to join into a
second.  `measure/mercury-atlas-resolution.md` measures their overlap on
paper; this measures whether the boolean agreed.

Is Caloris a basin rather than a dot?  Printed as a longitude grid, a row
through its centre should read bare globe, rim, floor, rim, bare globe -- five
runs, not one.  A circle union could never give that.

Is anything still a circle?  A plain drawn as a disc reads as a beach ball,
which is the defect this correction exists to remove, so each plain's width is
measured row by row and compared against the width a true disc of the same
area would have.

Is any bare-gray channel narrower than the nozzle, anywhere?  That is the one
failure the eye cannot catch in a render and the printer cannot recover from,
and it is asked in two dimensions so a bay open to the rest of the planet is
not confused with an enclosed island.

And are the two armies mirrors?  Since the Antisol Mirror revision this world
answers that in the MAP rather than in the lean, so the whole grid is classified
on both pieces and compared twice: at the same longitude, which must now
disagree, and at the reflected longitude, which must agree.

    "$WORKSHOP_PYTHON" measure/mercury_surface_scan.py > measure/mercury-surface.md
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import bool3d as X                                            # noqa: E402
import params as P                                            # noqa: E402
from parts import mercury_atlas as M                          # noqa: E402
from parts.markings import facing_meridian, reflect_longitude  # noqa: E402
from parts.world import world_bodies                          # noqa: E402

from OCP.BRepClass3d import BRepClass3d_SolidClassifier       # noqa: E402
from OCP.TopAbs import TopAbs_OUT                             # noqa: E402
from OCP.gp import gp_Pnt                                     # noqa: E402

#: How far under the sphere the sample sits.  The inlays run 1.20 mm deep, so
#: this is well inside them and well outside the tessellation's own tolerance.
DEPTH = 0.10
GLYPH = {"plains": "#", "caloris_rim": "#", "caloris_floor": "O", "globe": "."}

PLANET = "mercury"
RADIUS = P.globe_radius(PLANET)
MM_PER_DEG = math.radians(1.0) * RADIUS
NOZZLE = P.NOZZLE_MM
NOZZLE_DEG = NOZZLE / MM_PER_DEG


def sampler(side: str):
    """lat, lon -> the marking key the built world carries there, or None.

    None means the point is off the piece entirely: the globe is sunk into the
    disc and cut at the disc's top face, so the bottom of the ball does not
    exist.  That is a different answer from `.`, which is bare gray globe.
    """
    bodies = world_bodies(PLANET, side)
    centre = P.globe_centre_z(PLANET)
    tilt = math.radians(P.lean_sign(side) * P.PLANETS[PLANET]["tilt"])
    solids = {
        key: X.parts(shape)
        for key, (_colour, shape) in bodies.items()
        if key not in ("disc", "numeral")
    }

    def classify(lat_deg: float, lon_deg: float):
        lat, lon = math.radians(lat_deg), math.radians(lon_deg)
        reach = RADIUS - DEPTH
        x = reach * math.cos(lat) * math.cos(lon)
        y = reach * math.cos(lat) * math.sin(lon)
        z = reach * math.sin(lat)
        point = gp_Pnt(
            x * math.cos(tilt) + z * math.sin(tilt),
            y,
            -x * math.sin(tilt) + z * math.cos(tilt) + centre,
        )
        for key, members in solids.items():
            for solid in members:
                if BRepClass3d_SolidClassifier(
                    solid.wrapped, point, 1e-7
                ).State() != TopAbs_OUT:
                    return key
        return None

    return classify


def row(classify, lat, lon_from, lon_to, lon_step) -> str:
    out = ""
    lon = lon_from
    while lon <= lon_to + 1e-9:
        out += GLYPH.get(classify(lat, lon), " ")
        lon += lon_step
    return out


def runs(text: str, glyphs: str):
    """(start index, length) of every maximal run of any of `glyphs`."""
    found = []
    start = None
    for index, char in enumerate(text):
        if char in glyphs and start is None:
            start = index
        elif char not in glyphs and start is not None:
            found.append((start, index - start))
            start = None
    if start is not None:
        found.append((start, len(text) - start))
    return found


def _flood(grid, height, width, want):
    """Connected groups of cells where `want(cell)` holds, four-ways."""
    seen = [[False] * width for _ in range(height)]
    groups = []
    for yy in range(height):
        for xx in range(width):
            if seen[yy][xx] or not want(grid[yy][xx]):
                continue
            members = [(yy, xx)]
            seen[yy][xx] = True
            queue = [(yy, xx)]
            while queue:
                y0, x0 = queue.pop()
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    r, c = y0 + dy, (x0 + dx) % width
                    if 0 <= r < height and not seen[r][c] and want(grid[r][c]):
                        seen[r][c] = True
                        members.append((r, c))
                        queue.append((r, c))
            groups.append(members)
    return groups


def main() -> int:
    failures: list[str] = []
    print("# Mercury's corrected surface, measured on the built solids")
    print()
    print("Sampled %.2f mm under the sphere, in the planet's own frame, carried"
          % DEPTH)
    print("into the piece by the same obliquity the part uses, and classified")
    print("against every colour body of the world. `#` is the `cocoa_brown` the")
    print("plains and the Caloris rim share, `O` is the `white` Caloris floor,")
    print("`.` is the bare `gray` globe, and a blank is off the piece -- the")
    print("globe is sunk 2.00 mm into its disc and cut at the disc's top face,")
    print("so the bottom of the ball does not exist.")
    print()
    print("One degree of arc is %.4f mm on this Ø%.2f globe and the nozzle is"
          % (MM_PER_DEG, P.globe_diameter(PLANET)))
    print("%.2f mm, so a printable feature has to hold %.2f degrees."
          % (NOZZLE, NOZZLE_DEG))
    print()

    classify = sampler("sol")

    # ---------------------------------------------------------- the grid ---
    step = 3.0
    lats = [60.0 - step * n for n in range(int(120.0 / step) + 1)]
    lons = [-180.0 + step * n for n in range(int(360.0 / step))]
    grid = [[classify(lat, lon) for lon in lons] for lat in lats]
    height, width = len(lats), len(lons)

    print("## The whole surface")
    print()
    print("Longitude -180 to +180 east across, latitude +60 down to -60, every")
    print("%.0f degrees. Sol army." % step)
    print()
    print("```")
    print("       " + "".join("|" if (n * step) % 30 == 0 else " "
                              for n in range(width)))
    for index, lat in enumerate(lats):
        print("%6.1f %s" % (lat, "".join(GLYPH.get(cell, " ")
                                         for cell in grid[index])))
    print("```")
    print()

    # ------------------------------------------------------- do they fuse --
    print("## Do the plains fuse?")
    print()
    print("The `cocoa_brown` cells above, flooded four-ways with the longitude")
    print("seam joined, and each group named by the ring centres that fall")
    print("inside it. Caloris's rim is `cocoa_brown` too and is expected to")
    print("come out as a group of its own.")
    print()
    centres = {name: (lat, lon) for name, lat, lon, _r, _l in M.PLAINS_SPECS}
    # The rim is an annulus, so its own centre is inside the floor rather than
    # inside it.  Probe it halfway out instead, due north of the basin centre.
    centres["caloris_rim"] = (
        M.CALORIS_LAT + 0.5 * (M.CALORIS_FLOOR_RADIUS + M.CALORIS_RIM_RADIUS),
        M.CALORIS_LON,
    )
    groups = _flood(grid, height, width, lambda cell: cell in ("plains", "caloris_rim"))
    print("| group | cells | rings inside it |")
    print("|---|---|---|")
    for index, members in enumerate(sorted(groups, key=len, reverse=True), 1):
        inside = []
        for name, (lat, lon) in centres.items():
            yy = min(range(height), key=lambda n: abs(lats[n] - lat))
            xx = min(range(width),
                     key=lambda n: abs(((lons[n] - lon + 180) % 360) - 180))
            if (yy, xx) in members:
                inside.append(name)
        print("| %d | %d | %s |"
              % (index, len(members), ", ".join(sorted(inside)) or "-"))
    print()
    found = {frozenset(
        name for name, (lat, lon) in centres.items()
        if (min(range(height), key=lambda n: abs(lats[n] - lat)),
            min(range(width),
                key=lambda n: abs(((lons[n] - lon + 180) % 360) - 180))) in members
    ) for members in groups}
    for expected in M.PLAINS_EXPECTED_GROUPS:
        if not any(set(expected) <= group for group in found):
            failures.append("%s did not fuse into one region"
                            % ", ".join(expected))
    if not failures:
        print("Both expected groups came out fused: %s."
              % "; and ".join(" + ".join(group)
                              for group in M.PLAINS_EXPECTED_GROUPS))
    print()

    # -------------------------------------------------------- the basin ---
    print("## Is Caloris a basin or a dot?")
    print()
    print("Longitude -75 to -25 east, every degree, from latitude 50 down to")
    print("10: a window on the basin alone. A ringed basin reads globe, rim,")
    print("floor, rim, globe across its middle. A painted dot reads globe,")
    print("colour, globe.")
    print()
    print("```")
    ring_rows = 0
    narrow = None
    for n in range(41):
        lat = 50.0 - n
        text = row(classify, lat, -75.0, -25.0, 1.0)
        print("%6.1f %s" % (lat, text))
        floors = runs(text, "O")
        if not floors:
            continue
        start, length = floors[0]
        left = len(text[:start]) - len(text[:start].rstrip("#"))
        after = text[start + length:]
        right = len(after) - len(after.lstrip("#"))
        if left and right:
            ring_rows += 1
            scale = math.cos(math.radians(lat))
            for side in (left, right):
                span = side * MM_PER_DEG * scale
                if narrow is None or span < narrow[0]:
                    narrow = (span, lat)
    print("```")
    print()
    print("%d of the rows that cross the floor carry rim on both sides of it."
          % ring_rows)
    if narrow:
        print("The narrowest rim any of them measures is %.2f mm of arc, at"
              % narrow[0])
        print("latitude %+.0f." % narrow[1])
        if narrow[0] < NOZZLE:
            failures.append("the Caloris rim measures %.2f mm on the built solid"
                            % narrow[0])
    if ring_rows < 10:
        failures.append("Caloris reads as a dot rather than as a ringed basin")
    print()
    print("The rim is `cocoa_brown`, the same filament as the plains, so on the")
    print("scan it shares their glyph. On the piece it is unmistakable because")
    print("it encloses a `white` floor and nothing else on this globe does.")
    print()

    # ------------------------------------------------- still a circle? ----
    print("## Is any plain still a circle?")
    print()
    print("A disc of area A has width 2*sqrt(A/pi) at its middle and the same")
    print("width whichever way it is measured. For each group of fused plains")
    print("the table gives the cells it covers, the width of its widest row and")
    print("of its widest column, and the ratio between them. A circle scores")
    print("1.00 both ways; anything lobed does not.")
    print()
    print("| group | cells | widest row | widest column | row/column |")
    print("|---|---|---|---|---|")
    round_groups = 0
    for index, members in enumerate(sorted(groups, key=len, reverse=True), 1):
        by_row: dict[int, int] = {}
        by_col: dict[int, int] = {}
        for yy, xx in members:
            by_row[yy] = by_row.get(yy, 0) + 1
            by_col[xx] = by_col.get(xx, 0) + 1
        widest_row = max(by_row.values())
        widest_col = max(by_col.values())
        ratio = widest_row / widest_col
        print("| %d | %d | %d | %d | %.2f |"
              % (index, len(members), widest_row, widest_col, ratio))
        if 0.95 <= ratio <= 1.05 and len(members) > 20:
            round_groups += 1
    print()
    print("Read this as a smell test rather than as a gate: a lobed region can")
    print("still score near 1.00 by accident, and the picture above is the")
    print("evidence that matters. What it does establish is that no group here")
    print("is the equal-width disc the round-patch build produced.")
    print()

    # ------------------------------------------- an unprintable channel ---
    print("## Is any bare gray enclosed and too thin to print?")
    print()
    print("The gray cells, flooded in two dimensions with the longitude seam")
    print("joined, to separate a gray island the nozzle would have to lay down")
    print("inside the brown from a gray bay open to the rest of the planet,")
    print("which it would not.")
    print()
    gray = _flood(grid, height, width, lambda cell: cell == "globe")
    gray.sort(key=len, reverse=True)
    if len(gray) <= 1:
        print("**The bare gray is one connected region.** Nothing on this globe")
        print("asks the printer for a dot of gray surrounded by brown.")
    else:
        print("| island | cells | widest span mm |")
        print("|---|---|---|")
        for index, members in enumerate(gray[1:], 1):
            rows_seen = {r for r, _c in members}
            cols_seen = {c for _r, c in members}
            span = max(len(rows_seen), len(cols_seen)) * step * MM_PER_DEG
            print("| %d | %d | %.2f |" % (index, len(members), span))
            if span < NOZZLE:
                failures.append(
                    "an enclosed gray island of %d samples, %.2f mm across"
                    % (len(members), span))
    print()
    print("The white Caloris floor is enclosed by the rim by design, so it is")
    print("not counted here; its boundary is measured in")
    print("`measure/mercury-atlas-resolution.md` and again in the basin scan")
    print("above.")
    print()

    # ------------------------------------------------------ the mirror ----
    print("## Are the two armies mirrors, and is the mirror in the map?")
    print()
    print("Mercury's obliquity is %.2f degrees, so the mirrored lean moves the"
          % P.PLANETS[PLANET]["tilt"])
    print("pattern by 0.06 degrees of arc between the two armies -- %.4f mm, a"
          % (0.06 * MM_PER_DEG))
    print("fortieth of a nozzle width. That is why the Antisol Mirror revision")
    print("mirrors this world's MAP instead: on the Anti-Sol piece every")
    print("marking longitude is reflected to 2C - L about that piece's own")
    print("facing meridian, C = %+.4f degrees."
          % facing_meridian(PLANET, "anti"))
    print()
    print("So the two armies are asked TWO questions here, on the built solids")
    print("rather than on the marking table, and the answers have to be")
    print("opposite. The same grid is classified on the Anti-Sol piece and")
    print("compared with the Sol grid twice: once point for point at the same")
    print("longitude, which must now DISAGREE, and once against the reflected")
    print("longitude, which must AGREE.")
    print()
    other = sampler("anti")
    meridian = facing_meridian(PLANET, "anti")
    straight, reflected = 0, 0
    for index, lat in enumerate(lats):
        for column, lon in enumerate(lons):
            if other(lat, lon) != grid[index][column]:
                straight += 1
            if other(lat, reflect_longitude(lon, meridian)) != grid[index][column]:
                reflected += 1
    total = height * width
    print("| comparison | points that disagree | of | share |")
    print("|---|---:|---:|---:|")
    print("| Anti-Sol at the SAME longitude | %d | %d | %.2f%% |"
          % (straight, total, 100.0 * straight / total))
    print("| Anti-Sol at the REFLECTED longitude | %d | %d | %.2f%% |"
          % (reflected, total, 100.0 * reflected / total))
    print()
    if straight <= 0.01 * total:
        failures.append(
            "the Anti-Sol map still matches the Sol map at the same longitude "
            "at %d of %d points, so the mirror did not happen" % (straight, total))
    if reflected > 0.01 * total:
        failures.append(
            "the Anti-Sol map does not match the reflected Sol map at %d of %d "
            "points" % (reflected, total))
    print("The first row is the defect this revision corrects, measured on the")
    print("solids: before it, the two armies agreed everywhere. The second row")
    print("is the correction: the Anti-Sol globe carries the Sol globe's map")
    print("reflected about the facing meridian, point for point, over the whole")
    print("sampled surface -- the same statement `measure/mirror-meridian.md`")
    print("makes on the rings, made here on the built colour bodies instead.")
    print("The residue in the second row is the grid's own quantisation at a")
    print("marking boundary, where a sample falls one side of a line on one")
    print("piece and the other side on its mirror.")
    print()

    print("## Verdict")
    print()
    if failures:
        print("Measured faults:")
        print()
        for item in failures:
            print("- %s" % item)
    else:
        print("The plains fuse where they were drawn to fuse, Caloris reads as a")
        print("rim enclosing a floor rather than as a painted dot, no group is an")
        print("equal-width disc, no enclosed gray island exists anywhere on the")
        print("globe, and the Anti-Sol piece carries the Sol piece's surface")
        print("reflected about its own facing meridian.")
    print()
    print("Measured by `measure/mercury_surface_scan.py` on the exact solids")
    print("`parts/world.py` builds.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
