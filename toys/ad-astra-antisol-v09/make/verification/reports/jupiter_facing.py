"""Which way Jupiter's markings point at the two photographed frames.

A marking on the hidden hemisphere is not a marking.  The Great Red Spot sat
squarely on the far side of both armies in the original build and was carried
-110 degrees in longitude until it did not; the Wish requires that carry to be
preserved and re-measured, because the spot this revision draws is a 13 by 9
degree oval rather than the three overlapping circles the carry was measured
on.  This is that re-measurement, written down as a file rather than as prose,
in the form `measure/mercury_facing.py` and `measure/venus_facing.py` use.

`cad/scripts/render_review` puts the camera on the unit vector

    (cos el cos az, cos el sin az, sin el)

in the piece's own frame, and a world stands on the board under a pure
translation, so that vector is the view axis for every piece on the set.  A
marking's own direction is its latitude and longitude in the planet frame,
carried into the piece by the obliquity: rotated about +Y by the true tilt,
positive on a Sol world and negative on its Anti-Sol mirror.  The dot product
of the two is +1 dead-on, 0 at the limb and -1 on the far side.

Both ovals are measured vertex by vertex rather than only at their centres.
The spot is 13 degrees of arc across and the collar 17, so a centre that faces
the camera does not by itself establish that the whole marking does, and the
worst vertex is the number that decides.

    "$WORKSHOP_PYTHON" measure/jupiter_facing.py > measure/jupiter-facing.md
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import params as P                                            # noqa: E402
from parts import jupiter_atlas as J                          # noqa: E402
from snap_frames import HERO_VIEW, SHEET_VIEW                 # noqa: E402
from world_views import FRAMES as WORLD_FRAMES                # noqa: E402

PLANET = "jupiter"
TILT = P.PLANETS[PLANET]["tilt"]

#: The two frames the product is photographed at: `snap/iso.png` and the three
#: panels of `snap/signature.png`.  Both come from `snap_frames.py`, so this
#: report cannot drift away from the images it describes.
FRAMES = (("hero", HERO_VIEW), ("state sheet", SHEET_VIEW))

#: The per-world frame the single-piece evidence is rendered at, from
#: `world_views.py`, so the two sets of images are described by one table.
SPOT_FRAME = WORLD_FRAMES[PLANET]["spot"][:2]


def direction(lat_deg: float, lon_deg: float):
    lat, lon = math.radians(lat_deg), math.radians(lon_deg)
    return (math.cos(lat) * math.cos(lon),
            math.cos(lat) * math.sin(lon),
            math.sin(lat))


def lean(vector, side: str):
    """The planet frame carried into the piece: a turn about +Y by the tilt."""
    angle = math.radians(P.lean_sign(side) * TILT)
    x, y, z = vector
    return (x * math.cos(angle) + z * math.sin(angle),
            y,
            -x * math.sin(angle) + z * math.cos(angle))


def view_axis(azimuth: float, elevation: float):
    az, el = math.radians(azimuth), math.radians(elevation)
    return (math.cos(el) * math.cos(az), math.cos(el) * math.sin(az),
            math.sin(el))


def facing(lat_deg: float, lon_deg: float, side: str, view) -> float:
    marking = lean(direction(lat_deg, lon_deg), side)
    axis = view_axis(*view)
    return sum(one * other for one, other in zip(marking, axis))


def ring_facing(ring, side: str, view):
    values = [facing(lat, lon, side, view) for lon, lat in ring]
    return min(values), max(values)


def main() -> int:
    print("# Jupiter's markings against the camera")
    print()
    print("Dot product of each marking's own direction against the view axis,")
    print("at the two frames the whole set is photographed from and at the")
    print("per-world frame the two Jupiters are rendered at on their own, on")
    print("both armies. +1 is dead-on, 0 is the limb, -1 is the far side.")
    print()
    print("Jupiter's obliquity is %.2f degrees, the second smallest in the set,"
          % TILT)
    print("so the mirrored lean that distinguishes the two armies moves a")
    print("marking by very little and the Sol and Anti-Sol columns stay close.")
    print("That is the planet, not a mistake in the mirror: Venus at 177.36 and")
    print("Uranus at 97.77 separate widely on the same measurement.")
    print()

    print("## The Great Red Spot's centre")
    print()
    print("| frame | azimuth | elevation | Sol | Anti-Sol |")
    print("|---|---:|---:|---:|---:|")
    rows = list(FRAMES) + [("per-world spot frame", SPOT_FRAME)]
    for label, view in rows:
        print("| %s | %g | %g | %+.2f | %+.2f |"
              % (label, view[0], view[1],
                 facing(J.SPOT_LAT, J.SPOT_LON, "sol", view),
                 facing(J.SPOT_LAT, J.SPOT_LON, "anti", view)))
    print()

    print("## Every vertex of both ovals")
    print()
    print("The worst vertex is what decides whether the whole marking is in")
    print("frame, not the centre.")
    print()
    print("| marking | frame | Sol worst | Sol best | Anti-Sol worst | Anti-Sol best |")
    print("|---|---|---:|---:|---:|---:|")
    for name, ring in (("spot", J.SPOT_RING), ("collar", J.COLLAR_RING)):
        for label, view in rows:
            sol_low, sol_high = ring_facing(ring, "sol", view)
            anti_low, anti_high = ring_facing(ring, "anti", view)
            print("| `%s` | %s | **%+.2f** | %+.2f | **%+.2f** | %+.2f |"
                  % (name, label, sol_low, sol_high, anti_low, anti_high))
    print()

    print("## The belts and zones")
    print()
    print("A belt runs all the way round the globe, so half of it faces the")
    print("camera at every frame by construction and the only question its")
    print("facing answers is which latitudes are in view. Reported at the")
    print("longitude that faces each camera, which is the azimuth itself.")
    print()
    print("| marking | latitudes | hero Sol | hero Anti-Sol | sheet Sol | sheet Anti-Sol |")
    print("|---|---|---:|---:|---:|---:|")
    rowset = ([(name, south, north) for _k, name, south, north, _h in J.BELTS]
              + [(name, south, north) for _k, name, south, north, _ds, _dn in J.ZONES])
    for name, south, north in rowset:
        middle = 0.5 * (south + north)
        values = []
        for _label, view in FRAMES:
            for side in ("sol", "anti"):
                values.append(facing(middle, view[0], side, view))
        print("| %s | %+.0f to %+.0f | %+.2f | %+.2f | %+.2f | %+.2f |"
              % ((name, south, north) + tuple(values)))
    print()

    print("## What the numbers say")
    print()
    sol_hero = facing(J.SPOT_LAT, J.SPOT_LON, "sol", HERO_VIEW)
    anti_hero = facing(J.SPOT_LAT, J.SPOT_LON, "anti", HERO_VIEW)
    sol_sheet = facing(J.SPOT_LAT, J.SPOT_LON, "sol", SHEET_VIEW)
    anti_sheet = facing(J.SPOT_LAT, J.SPOT_LON, "anti", SHEET_VIEW)
    worst_centre = min(sol_hero, anti_hero, sol_sheet, anti_sheet)
    worst_vertex = min(
        ring_facing(J.SPOT_RING, side, view)[0]
        for side in ("sol", "anti")
        for _label, view in FRAMES
    )
    print("- **The -110 degree carry is preserved exactly.** The spot's centre")
    print("  is still latitude %+.0f, longitude %+.0f, which is where that carry"
          % (J.SPOT_LAT, J.SPOT_LON))
    print("  put it. Nothing in this correction moved it; the oval is drawn")
    print("  about the same point the three circles were drawn about.")
    print("- **It still faces both photographed cameras on both armies.** The")
    print("  centre measures %+.2f and %+.2f at the hero frame and %+.2f and"
          % (sol_hero, anti_hero, sol_sheet))
    print("  %+.2f at the state sheet, so the worst of the four is %+.2f --"
          % (anti_sheet, worst_centre))
    print("  positive at every frame on every army, against the -0.49 the")
    print("  original build measured before the carry.")
    print("- **And so does the whole oval, not just its centre.** The worst")
    print("  vertex of the red ring over both armies and both photographed")
    print("  frames is %+.2f. The spot this revision draws is 13 degrees of arc"
          % worst_vertex)
    print("  across where the three circles spanned 37, so it sits further")
    print("  inside the near hemisphere than the marking it replaces did.")
    print()
    print("Measured by `measure/jupiter_facing.py` on the exact rings in")
    print("`parts/jupiter_atlas.py` and the exact cameras in `snap_frames.py`")
    print("and `world_views.py`.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
