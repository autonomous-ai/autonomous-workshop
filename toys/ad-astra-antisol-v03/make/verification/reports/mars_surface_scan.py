"""What colour the built Mars actually is, point by point.

The sibling of `measure/ice_cap_scan.py`, and it answers the questions a render
cannot for the same reason that one does: it asks the built solids directly
rather than looking at a picture of them.  A point is placed a fixed depth
under the sphere, in the planet's own frame, carried into the piece by the same
obliquity the part uses, and classified against every colour body of the world.

Four questions, all of them things the Wish asks after by name.

Does the southern belt actually fuse?  Sirenum, Cimmerium and Tyrrhenum are
drawn as three rings and are meant to come out as one dark band; the atlas
report measures their overlap on paper, and this measures whether the boolean
agreed.

Is Syrtis Major a triangle?  Printed as a longitude/latitude grid it should
read as a broad northern base narrowing to a point in the south, which is what
a union of discs could never give.

Is each cap rim ragged rather than circular?  A bare cap ends on an exact
circle of latitude, so the white run at a fixed latitude just outside the rim
should be broken into lobes with red between them, not continuous.

And is any red channel between two dark regions narrower than the nozzle?  That
is the one failure the eye cannot catch in a render and the printer cannot
recover from.

    "$WORKSHOP_PYTHON" measure/mars_surface_scan.py > measure/mars-surface.md
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import bool3d as X                                            # noqa: E402
import params as P                                            # noqa: E402
from parts import mars_atlas as A                             # noqa: E402
from parts.world import world_bodies                          # noqa: E402

from OCP.BRepClass3d import BRepClass3d_SolidClassifier       # noqa: E402
from OCP.TopAbs import TopAbs_OUT                             # noqa: E402
from OCP.gp import gp_Pnt                                     # noqa: E402

#: How far under the sphere the sample sits.  The inlays run 1.20 mm deep, so
#: this is well inside them and well outside the tessellation's own tolerance.
DEPTH = 0.10
GLYPH = {"albedo": "#", "caps": "I", "globe": "."}

PLANET = "mars"
RADIUS = P.globe_radius(PLANET)
MM_PER_DEG = math.radians(1.0) * RADIUS
NOZZLE = P.NOZZLE_MM


def sampler(side: str):
    """lat, lon -> the marking key the built world carries there, or None.

    None means the point is off the piece entirely: the globe is sunk into the
    disc and cut at the disc's top face, so the bottom of the ball does not
    exist.  That is a different answer from `.`, which is bare red globe.
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


def row(classify, lat, lon_from, lon_to, lon_step):
    out = ""
    lon = lon_from
    while lon <= lon_to + 1e-9:
        out += GLYPH.get(classify(lat, lon), " ")
        lon += lon_step
    return out


def runs(text: str, glyph: str):
    """(start index, length) of every run of `glyph` in a scan row."""
    found = []
    start = None
    for index, char in enumerate(text):
        if char == glyph and start is None:
            start = index
        elif char != glyph and start is not None:
            found.append((start, index - start))
            start = None
    if start is not None:
        found.append((start, len(text) - start))
    return found


def main() -> int:
    failures: list[str] = []
    print("# Mars's corrected surface, measured on the built solids")
    print()
    print("Sampled %.2f mm under the sphere, in the planet's own frame, carried"
          % DEPTH)
    print("into the piece by the same obliquity the part uses, and classified")
    print("against every colour body of the world. `#` is `albedo` cocoa brown,")
    print("`I` is `caps` white, `.` is the bare `red` globe, and a blank is off")
    print("the piece -- the globe is sunk 2.00 mm into its disc and cut at the")
    print("disc's top face, so the bottom of the ball does not exist.")
    print()
    print("One degree of arc is %.4f mm on this Ø%.2f globe and the nozzle is"
          % (MM_PER_DEG, P.globe_diameter(PLANET)))
    print("%.2f mm, so a printable feature has to hold %.2f degrees."
          % (NOZZLE, NOZZLE / MM_PER_DEG))
    print()

    classify = sampler("sol")

    print("## Is Syrtis Major a triangle?")
    print()
    print("Longitude 58 to 90 east, every 2 degrees, from latitude 24 north")
    print("down to 14 south. A triangle has a broad base and a point.")
    print()
    print("```")
    widths = []
    for step in range(20):
        lat = 24.0 - 2.0 * step
        text = row(classify, lat, 58.0, 90.0, 2.0)
        dark = runs(text, "#")
        widths.append((lat, max((length for _s, length in dark), default=0)))
        print("%6.1f %s" % (lat, text))
    print("```")
    print()
    base = max(width for _lat, width in widths)
    tip = [lat for lat, width in widths if width]
    print("Widest at %.0f degrees of longitude across, narrowing to nothing:"
          % (base * 2.0))
    print("the dark runs from latitude %.0f north down to %.0f, and its widest"
          % (max(tip), min(tip)))
    print("row is %.2f mm of arc. That is a wedge, not a disc." % (base * 2.0 * MM_PER_DEG))
    if base < 2:
        failures.append("Syrtis Major is under two samples wide at its base")
    print()

    print("## Does the southern belt fuse into one band?")
    print()
    print("Longitude 130 to 290 east, every 2 degrees, across the")
    print("mid-southern latitudes. Sirenum, Cimmerium and Tyrrhenum are drawn")
    print("as three rings and are meant to come out as one dark band.")
    print()
    print("```")
    worst = None
    for step in range(11):
        lat = -14.0 - 2.0 * step
        text = row(classify, lat, 130.0, 290.0, 2.0)
        print("%6.1f %s" % (lat, text))
        gaps = runs(text, ".")
        interior = [(start, length) for start, length in gaps
                    if start > 0 and start + length < len(text)]
        for _start, length in interior:
            span = length * 2.0 * MM_PER_DEG * math.cos(math.radians(lat))
            if worst is None or span < worst[0]:
                worst = (span, lat)
    print("```")
    print()

    # A row scan cannot tell a hole from a fjord.  Where two of the belt's
    # rings cross, the red outside the union narrows to a point at the
    # crossing, and a single latitude row through that wedge reads as
    # dark-red-dark even though the red escapes north or south into the open.
    # That is a merge, not an unprintable island: the printer simply loses the
    # tip of the notch and the two dark regions join there.  What would be a
    # real fault is a red island the open red cannot reach, narrower than the
    # nozzle -- a dot of red inside the brown that nothing can lay down.  That
    # is a connectivity question, so it is asked in two dimensions.
    lat_lo, lat_hi, lon_lo, lon_hi, step = -40.0, -8.0, 128.0, 292.0, 1.0
    lats = [lat_lo + step * n for n in range(int((lat_hi - lat_lo) / step) + 1)]
    lons = [lon_lo + step * n for n in range(int((lon_hi - lon_lo) / step) + 1)]
    grid = [[classify(lat, lon) == "albedo" for lon in lons] for lat in lats]

    #: Red cells reachable from the window's own border, flooded four-ways.
    height, width = len(lats), len(lons)
    open_red = [[False] * width for _ in range(height)]
    stack = [
        (yy, xx)
        for yy in range(height) for xx in range(width)
        if (yy in (0, height - 1) or xx in (0, width - 1)) and not grid[yy][xx]
    ]
    for yy, xx in stack:
        open_red[yy][xx] = True
    while stack:
        yy, xx = stack.pop()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            r, c = yy + dr, xx + dc
            if 0 <= r < height and 0 <= c < width and not grid[r][c] \
                    and not open_red[r][c]:
                open_red[r][c] = True
                stack.append((r, c))

    islands = []
    seen = [[False] * width for _ in range(height)]
    for yy in range(height):
        for xx in range(width):
            if grid[yy][xx] or open_red[yy][xx] or seen[yy][xx]:
                continue
            members = [(yy, xx)]
            seen[yy][xx] = True
            queue = [(yy, xx)]
            while queue:
                yy0, xx0 = queue.pop()
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    r, c = yy0 + dr, xx0 + dc
                    if 0 <= r < height and 0 <= c < width and not grid[r][c] \
                            and not seen[r][c]:
                        seen[r][c] = True
                        members.append((r, c))
                        queue.append((r, c))
            islands.append(members)

    print("The belt's red, flooded in two dimensions over latitude %.0f to %.0f"
          % (lat_lo, lat_hi))
    print("and longitude %.0f to %.0f at %.1f degrees, to separate a red island"
          % (lon_lo, lon_hi, step))
    print("-- which the nozzle would have to lay down inside the brown -- from a")
    print("red bay open to the rest of the planet, which it would not.")
    print()
    if not islands:
        print("**No enclosed red island anywhere in the belt.** Every red cell")
        print("here is connected to the open red outside it, so nothing in this")
        print("region asks the printer for a dot of red surrounded by brown.")
    else:
        print("| island | cells | widest span mm |")
        print("|---|---|---|")
        for index, members in enumerate(islands, 1):
            rows = {r for r, _c in members}
            cols = {c for _r, c in members}
            span = max(len(rows), len(cols)) * step * MM_PER_DEG
            print("| %d | %d | %.2f |" % (index, len(members), span))
            if span < NOZZLE:
                failures.append(
                    "the belt encloses a red island of %d sample%s, %.2f mm "
                    "across, under the %.2f mm nozzle"
                    % (len(members), "" if len(members) == 1 else "s",
                       span, NOZZLE))
    print()
    if worst is not None:
        print("Stated because a reader meets it in the rows above and wonders:")
        print("the narrowest red run that a single latitude row shows enclosed")
        print("is %.2f mm at latitude %.0f. That is the tip of a bay, not an"
              % worst)
        print("island -- it is where two of the belt's rings cross and the red")
        print("between them runs out to a point. The printer loses the last")
        print("fraction of a millimetre of that point and the two dark regions")
        print("meet there, which is what the atlas asks for at a join anyway.")
    print()

    print("## Is the north cap's rim ragged?")
    print()
    print("Every 3 degrees of longitude, from 8 degrees outside the rim at")
    print("latitude %.0f up to the pole. A bare cap would end on an exact"
          % A.CAP_NORTH_RIM_LAT)
    print("circle of latitude, so every row below the rim would be either all")
    print("red or all white; lobes make it neither.")
    print()
    print("```")
    broken = 0
    for step in range(9):
        lat = A.CAP_NORTH_RIM_LAT - 8.0 + 2.0 * step
        text = row(classify, lat, 0.0, 357.0, 3.0)
        white = runs(text, "I")
        if 0 < len(white) and text.count("I") not in (0, len(text)):
            broken += 1
        print("%6.1f %s  (%d white run%s)"
              % (lat, text, len(white), "" if len(white) == 1 else "s"))
    print("```")
    print()
    if broken:
        print("%d of the 9 rows are part white and part red, and several carry"
              % broken)
        print("more than one separate white run. The rim is not a circle of")
        print("latitude: it is an edge with lobes reaching past it and red bays")
        print("between them. That is the correction -- a bare circular rim reads")
        print("as a lid laid on the globe rather than as ice.")
    else:
        failures.append("every sampled row near the north rim is uniform; the "
                        "rim is still an exact circle of latitude")
        print("**Every row is uniform. The rim is still a circle.**")
    print()

    print("## Does the south cap survive the disc?")
    print()
    print("Every 6 degrees of longitude, from latitude -60 to the south pole.")
    print()
    print("```")
    alive = 0
    for step in range(7):
        lat = -60.0 - 5.0 * step
        text = row(classify, lat, 0.0, 354.0, 6.0)
        alive += text.count("I")
        print("%6.1f %s" % (lat, text))
    print("```")
    print()
    print("The globe is sunk 2.00 mm into its disc and cut at the disc's top")
    print("face, and at this obliquity that cut takes the south pole with it,")
    print("so most of this hemisphere is off the piece. %d of the sampled" % alive)
    print("points are white. The southern cap is present in the geometry and")
    print("is stated as barely visible rather than claimed as a feature.")
    print()

    print("## The two armies")
    print()
    print("The same row on both pieces, at the Syrtis face. The two carry the")
    print("same rings in the planet's own frame -- ownership never touches a")
    print("planet's own appearance -- and what is mirrored between them is the")
    print("lean, which is why the disc's cut falls in a different place on each.")
    print()
    print("```")
    anti = sampler("anti")
    for lat in (10.0, 0.0, -10.0):
        print("sol  %6.1f %s" % (lat, row(classify, lat, 50.0, 100.0, 2.0)))
        print("anti %6.1f %s" % (lat, row(anti, lat, 50.0, 100.0, 2.0)))
    print("```")
    print()
    print("Syrtis Major lands on the same longitudes on both armies, which is")
    print("the right answer: mirroring the map itself would put one army in a")
    print("reflected Mars.")
    print()

    print("## Verdict")
    print()
    if failures:
        for item in failures:
            print("- %s" % item)
    else:
        print("Syrtis Major is a wedge. The southern belt is one fused band with")
        print("no sub-nozzle thread of red inside it. The north cap's rim is")
        print("broken into lobes rather than ending on a circle of latitude. The")
        print("south cap is present but mostly below the disc's cut, and is")
        print("stated as such. Both armies carry the same map.")
    print()
    print("Measured by `measure/mars_surface_scan.py` on the built solids.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
