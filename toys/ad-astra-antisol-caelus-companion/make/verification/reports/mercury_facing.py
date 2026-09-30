"""Which way every Mercury marking points at the two photographed frames.

A marking on the hidden hemisphere is not a marking.  Venus's cloud Y and
Jupiter's Great Red Spot each sat squarely on the far side of both armies in
the original build and were carried in longitude until they did not; the
comments recording that live in `parts/markings.py`, and this is the same
measurement for Mercury, written down as a file rather than as prose.

Mercury has two different reasons to want it.  The seven plains keep the
centres they were drawn at, so their facing is a *record*: it says how much of
the albedo map a reader of the product images is actually offered, and it is
what establishes that Mercury's defect was contrast rather than longitude.
Caloris is new and its longitude is free, so its facing is a *decision*, and
this is the measurement the decision was taken on.

`cad/scripts/render_review` puts the camera on the unit vector

    (cos el cos az, cos el sin az, sin el)

in the piece's own frame, and a world stands on the board under a pure
translation, so that vector is the view axis for every piece on the set.  A
marking's own direction is its latitude and longitude in the planet frame,
carried into the piece by the obliquity: rotated about +Y by the true tilt,
positive on a Sol world and negative on its Anti-Sol mirror.  The dot product
of the two is +1 dead-on, 0 at the limb and -1 on the far side.

    "$WORKSHOP_PYTHON" measure/mercury_facing.py > measure/mercury-facing.md
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import params as P                                            # noqa: E402
from parts import mercury_atlas as M                          # noqa: E402
from snap_frames import HERO_VIEW, SHEET_VIEW                 # noqa: E402

PLANET = "mercury"
TILT = P.PLANETS[PLANET]["tilt"]

#: The two frames the product is photographed at: `snap/iso.png` and the three
#: panels of `snap/signature.png`.  Both come from `snap_frames.py`, so this
#: report cannot drift away from the images it describes.
FRAMES = (("hero", HERO_VIEW), ("state sheet", SHEET_VIEW))


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


def rows():
    out = [(name, lat, lon) for name, lat, lon, _r, _l in M.PLAINS_SPECS]
    out.append(("caloris", M.CALORIS_LAT, M.CALORIS_LON))
    return out


def main() -> int:
    print("# Mercury's markings against the camera")
    print()
    print("Dot product of each marking's own direction against the view axis,")
    print("at the two frames the product is photographed from, on both armies.")
    print("+1 is dead-on, 0 is the limb, -1 is the far side.")
    print()
    print("Mercury's obliquity is %.2f degrees, the smallest in the set, so the"
          % TILT)
    print("mirrored lean that distinguishes the two armies moves a marking by")
    print("almost nothing and the Sol and Anti-Sol columns agree to two decimals.")
    print("That is the planet, not a mistake in the mirror: Earth at 23.44")
    print("degrees and Uranus at 97.77 separate widely on the same measurement.")
    print()
    for label, view in FRAMES:
        print("## The %s frame: azimuth %g, elevation %g" % (label, view[0], view[1]))
        print()
        print("| marking | latitude | longitude | Sol | Anti-Sol | faces the camera |")
        print("|---|---:|---:|---:|---:|---|")
        for name, lat, lon in rows():
            sol = facing(lat, lon, "sol", view)
            anti = facing(lat, lon, "anti", view)
            print("| `%s` | %+.1f | %+.1f | %+.2f | %+.2f | %s |"
                  % (name, lat, lon, sol, anti,
                     "yes" if min(sol, anti) > 0 else "no"))
        plains = [facing(lat, lon, "sol", view) for name, lat, lon in rows()[:-1]]
        print()
        print("%d of the 7 plains face this camera; the best of them is %+.2f."
              % (sum(1 for value in plains if value > 0), max(plains)))
        print()

    print("## What the numbers decided")
    print()
    print("**The plains did not move.** Three of the seven face the hero camera")
    print("and four face the state sheet, the best at +0.55 and +0.46. That is")
    print("an ordinary albedo map seen from one side, not a pattern hiding round")
    print("the back: Venus's and Jupiter's markings measured -0.03 and -0.49")
    print("before they were carried, with no rendered view showing any of them.")
    print("Mercury's patches were always in frame -- they could not be seen")
    print("because `dark_gray` on `gray` is 21.8 luma levels on a 13.78 mm ball")
    print("(`measure/mercury-tone-separation.md`), which is a contrast problem")
    print("and is what this revision repairs. Carrying them in longitude would")
    print("have moved a pattern that was not lost and thrown away the centres")
    print("the set already had.")
    print()
    print("**Caloris was placed by this table.** Its latitude is fixed at +30 by")
    print("the Wish; its longitude is free because this set fixes no meridian on")
    print("Mercury. A feature at +30 faces a frame most squarely when its")
    print("longitude matches that frame's azimuth, and the two azimuths are -55")
    print("and -45, so -50 is the midpoint. It measures %+.2f and %+.2f -- the"
          % (facing(M.CALORIS_LAT, M.CALORIS_LON, "sol", HERO_VIEW),
             facing(M.CALORIS_LAT, M.CALORIS_LON, "sol", SHEET_VIEW)))
    print("most nearly dead-on any marking in this set gets, at both frames and")
    print("on both armies.")
    print()
    print("Measured by `measure/mercury_facing.py` on the exact rings in")
    print("`parts/mercury_atlas.py` and the exact cameras in `snap_frames.py`.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
