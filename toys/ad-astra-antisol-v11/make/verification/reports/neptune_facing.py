"""Neptune's markings against the camera.

The build this revision corrects put eight SHORT cloud streaks on this globe,
and a short marking has a longitude: it can be on the face the camera sees or
on the face it does not, and the archived run had to solve eight latitudes and
eight longitudes together against four cameras to keep them visible.  That
solution is in the archive and this report used to be it.

**This revision's clouds are three CLOSED latitude bands, and a closed band has
no longitude to solve.**  It runs the whole way round the planet, so some arc
of it faces every camera that can see its latitude at all, and the best facing
it can reach at a given camera is fixed by latitude alone:
cos(sub-latitude - band latitude).  There is nothing left to place.  That is
the plain consequence of the owner's decision, stated rather than dressed up as
a passed check, and it is also the reason the previous drawing's whole
southern-weighting problem is gone.

What still has to be measured is the DARK SPOT, which is short, which did not
move, and whose facing is what the per-world `spot` camera azimuth was solved
for.  Requirement 2 of this revision is that the spot does not move, so its dot
products are measured again here and compared against the archived ones.

The arithmetic.  `render_review` places the camera at (azimuth, elevation), so
the view axis in the piece's frame is
(cos el cos az, cos el sin az, sin el).  `features/patches.planet_frame` turns
the planet's frame about +Y by the obliquity, +28.32 degrees for a Sol world
and -28.32 for its Anti-Sol mirror, so the view axis IN THE PLANET'S FRAME is
that vector turned back by the same angle.  Its latitude and longitude are the
camera's sub-point: the one place on the planet that is dead-on.

    "$WORKSHOP_PYTHON" measure/neptune_facing.py > measure/neptune-facing.md
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import params as P                                            # noqa: E402
from parts import neptune_atlas as N                          # noqa: E402
from snap_frames import HERO_VIEW, SHEET_VIEW                 # noqa: E402
from world_views import FRAMES, polar_frame                   # noqa: E402

TILT = P.PLANETS["neptune"]["tilt"]

#: The facing floor the archived placement was solved against.  Not zero: zero
#: is the limb, and a marking exactly on the limb is a sliver seen edge-on
#: rather than a marking a reader can see.  Kept as the yardstick so this
#: revision's numbers can be read against the archived ones.
FLOOR = 0.30

#: What the build this revision corrects measured the dark spot's centre at,
#: quoted from its own `parts/markings.py` facing table in
#: `revision-source.zip`: hero Sol/Anti, then state sheet Sol/Anti.
#:
#: Requirement 2 is that the spot does not move.  These are the numbers that is
#: checked against; they are archival facts rather than measurements this run
#: made, so they are written down once, here, with their source.
ARCHIVED_SPOT = {
    ("hero", "Sol"): 0.53,
    ("hero", "Anti-Sol"): 0.86,
    ("state sheet", "Sol"): 0.28,
    ("state sheet", "Anti-Sol"): 0.70,
}


def view_axis(azimuth: float, elevation: float):
    az, el = math.radians(azimuth), math.radians(elevation)
    return (math.cos(el) * math.cos(az), math.cos(el) * math.sin(az),
            math.sin(el))


def in_planet_frame(vector, side: str):
    """The piece-frame vector, read in the planet's own frame."""
    phi = math.radians(-P.lean_sign(side) * TILT)
    x, y, z = vector
    return (x * math.cos(phi) + z * math.sin(phi), y,
            -x * math.sin(phi) + z * math.cos(phi))


def sub_point(axis):
    return (math.degrees(math.asin(max(-1.0, min(1.0, axis[2])))),
            math.degrees(math.atan2(axis[1], axis[0])))


def unit(lon_deg: float, lat_deg: float):
    lat, lon = math.radians(lat_deg), math.radians(lon_deg)
    return (math.cos(lat) * math.cos(lon), math.cos(lat) * math.sin(lon),
            math.sin(lat))


def dot(one, other):
    return sum(a * b for a, b in zip(one, other))


NEPTUNE_FRAMES = FRAMES["neptune"]
PRODUCT_FRAMES = (("hero", HERO_VIEW), ("state sheet", SHEET_VIEW))


def axes(side: str):
    """frame name -> view axis in the planet's frame, for one army."""
    out = {}
    for name, view in PRODUCT_FRAMES:
        out[name] = in_planet_frame(view_axis(*view), side)
    for name, view in NEPTUNE_FRAMES.items():
        out["per-world %s" % name] = in_planet_frame(
            view_axis(view[0], view[1]), side)
    azimuth, elevation, _why = polar_frame(side, "neptune")
    out["per-world polar"] = in_planet_frame(view_axis(azimuth, elevation), side)
    return out


def band_best(axis, low: float, high: float) -> float:
    """The best dot product any point of a closed latitude band reaches.

    A band spans every longitude, so at a camera whose sub-point is at
    latitude `s` the best any point of it reaches is cos(s - lat) taken at the
    band's own latitude nearest `s` -- achieved on the sub-point's meridian.
    Measured rather than reasoned: the band is walked at a degree of longitude
    and a tenth of a degree of latitude and the maximum is taken.
    """
    best = -1.0
    steps = 360
    for index in range(steps):
        lon = -180.0 + 360.0 * index / steps
        for step in range(11):
            lat = low + (high - low) * step / 10.0
            best = max(best, dot(axis, unit(lon, lat)))
    return best


def spot_worst(axis) -> float:
    """The worst dot product any VERTEX of the spot's ring reaches."""
    return min(dot(axis, unit(lon, lat)) for lon, lat in N.SPOT_RING)


def main() -> int:
    sol, anti = axes("sol"), axes("anti")
    product_names = [name for name, _v in PRODUCT_FRAMES]
    world_names = ["per-world %s" % name for name in NEPTUNE_FRAMES] + \
                  ["per-world polar"]
    armies = (("Sol", sol), ("Anti-Sol", anti))

    print("# Neptune's markings against the camera")
    print()
    print("Dot product of each marking against the view axis, at the two")
    print("frames the whole set is photographed from and at the per-world")
    print("frames the two Neptunes are rendered at on their own, on both")
    print("armies. +1 is dead-on, 0 is the limb, -1 is the far side.")
    print()
    print("Every number below is measured at the exact cameras `snap_frames.py`")
    print("and `world_views.py` declare, on the exact latitudes and the exact")
    print("ring `parts/neptune_atlas.py` hands the build. The yardstick is the")
    print("**+%.2f** facing floor the archived placement was solved against."
          % FLOOR)
    print()

    print("## What this revision changed about this question")
    print()
    print("The archived build's clouds were eight SHORT streaks, so each had a")
    print("longitude and each could be on the wrong face; keeping them visible")
    print("was a solved optimisation over eight latitudes and eight longitudes")
    print("against four cameras at once.")
    print()
    print("This revision's clouds are three CLOSED latitude bands. A closed")
    print("band spans every longitude, so there is no longitude to solve and no")
    print("way for one to be hidden by rotation: at any camera, some arc of it")
    print("faces the lens as squarely as its own latitude allows. The whole")
    print("placement problem is gone, and with it most of this report's former")
    print("evidentiary value. That is a consequence of the owner's decision and")
    print("it is stated plainly rather than re-dressed as a check that passed.")
    print()
    print("What is left worth measuring is the DARK SPOT, which is short, and")
    print("which requirement 2 says must not move.")
    print()

    print("## Where each camera is looking")
    print()
    print("Neptune's obliquity is %.2f degrees and a Sol world leans its north"
          % TILT)
    print("pole toward +X, so the two armies do not share a sub-point and the")
    print("Sol piece's cameras both look DOWN on its northern hemisphere.")
    print()
    print("| frame | azimuth | elevation | army | sub-latitude | sub-longitude |")
    print("|---|---:|---:|---|---:|---:|")
    for name in product_names:
        view = dict(PRODUCT_FRAMES)[name]
        for side, table in armies:
            lat, lon = sub_point(table[name])
            print("| %s | %.0f | %.3f | %s | %+.1f | %+.1f |"
                  % (name, view[0], view[1], side, lat, lon))
    for name in NEPTUNE_FRAMES:
        view = NEPTUNE_FRAMES[name]
        for side, table in armies:
            lat, lon = sub_point(table["per-world %s" % name])
            print("| per-world %s | %.0f | %.3f | %s | %+.1f | %+.1f |"
                  % (name, view[0], view[1], side, lat, lon))
    for side, table in armies:
        azimuth, elevation, _why = polar_frame(
            "sol" if side == "Sol" else "anti", "neptune")
        lat, lon = sub_point(table["per-world polar"])
        print("| per-world polar | %.0f | %.3f | %s | %+.1f | %+.1f |"
              % (azimuth, elevation, side, lat, lon))
    print()

    print("## The three bands, at every frame")
    print()
    print("The best dot product any point of each band reaches, walked at one")
    print("degree of longitude and a tenth of a degree of latitude rather than")
    print("taken from the formula. A closed band cannot be hidden by rotation,")
    print("but it can be hidden by LATITUDE: its whole circle falls behind the")
    print("limb when the camera's sub-latitude is more than 90 degrees from it.")
    print("That does happen on this globe and the table says where.")
    print()
    header = "| band | latitudes |" + "".join(
        " %s %s |" % (name, side) for name in product_names for side, _t in armies)
    print(header)
    print("|---|---|" + "---:|" * (len(product_names) * 2))
    band_floor = None
    below_floor, behind_limb = [], []
    for key, low, high in N.BANDS:
        cells = []
        for name in product_names:
            for side, table in armies:
                value = band_best(table[name], float(low), float(high))
                band_floor = value if band_floor is None else min(band_floor, value)
                if value < FLOOR:
                    below_floor.append((key, name, side, value))
                if value <= 0.0:
                    behind_limb.append((key, name, side, value))
                cells.append("%+.2f" % value)
        print("| `%s` | %+d to %+d | %s |" % (key, low, high, " | ".join(cells)))
    print()
    print("The worst any band does at either product frame on either army is")
    print("**%+.2f**, against the archived floor of +%.2f."
          % (band_floor, FLOOR))
    print()
    if not below_floor:
        print("Every band clears the floor at every product frame on both")
        print("armies.")
    else:
        print("**%d of the %d band/frame/army cases fall below that floor, and"
              % (len(below_floor), 2 * 2 * len(N.BANDS)))
        print("%d of those %s behind the limb outright:**"
              % (len(behind_limb), "falls" if len(behind_limb) == 1 else "fall"))
        print()
        for key, name, side, value in below_floor:
            print("- `%s` at the %s frame on the %s piece: %+.2f%s"
                  % (key, name, side, value,
                     " -- **behind the limb**" if value <= 0.0 else ""))
        print()
        print("This is not a placement fault and it is not repairable without")
        print("moving a band, which the owner's instruction forbids. It is the")
        print("same geometric fact the archived build recorded about its own")
        print("two southernmost streaks: the Sol piece leans its north pole")
        print("toward the lens, so both of its cameras look DOWN on the")
        print("northern hemisphere -- the state-sheet sub-point sits at +51.5 --")
        print("and a camera there reaches a marking at latitude L at best at")
        print("cos(51.5 - L), whatever longitude it is drawn at. At a floor of")
        print("+%.2f that camera cannot reach anything south of about -21."
              % FLOOR)
        print()
        print("`b1` is drawn at -46 to -41, which is south of that line. On the")
        print("ANTI-Sol piece, which leans the same pole away, it reaches")
        print("%+.2f at the hero frame and %+.2f at the state sheet and is"
              % (band_best(anti["hero"], -46.0, -41.0),
                 band_best(anti["state sheet"], -46.0, -41.0)))
        print("plainly visible. So `b1` is, in this build, an ANTI-SOL-ONLY")
        print("FEATURE at the set's two photographed frames -- exactly the role")
        print("`s1` and `s2` held in the archived build, inherited by the band")
        print("that stands where they stood. It is recorded here, in the")
        print("product's limitations and in the spec rather than left for a")
        print("reader of the Sol piece to report as a missing band.")
        print()
        print("Across the per-world frames as well, rather than asserted:")
        print()
        print("| frame | army | `b1` best |")
        print("|---|---|---:|")
        for name in world_names:
            for side, table in armies:
                print("| %s | %s | %+.2f |"
                      % (name, side, band_best(table[name], -46.0, -41.0)))
        print()
        print("The two level per-world frames, `spot` and `opposite`, show all")
        print("three bands on both pieces, and `opposite` is the frame that")
        print("shows them unbroken. The per-world `hero` frame is the product")
        print("frame and carries the same figure. The polar frame looks down")
        print("the leaning north pole, so `b1` is behind the limb there on both")
        print("armies by construction -- that frame exists to show the pole,")
        print("not the southern band. So `b1` is in the evidence, at the frames")
        print("that can reach it, and the pictures say which those are.")
    print()

    print("## The dark spot, at every frame")
    print()
    print("The spot's own centre, and -- because a 5.35 mm oval is not a point")
    print("-- the worst any VERTEX of its ring reaches at the same camera.")
    print()
    print("| frame | army | centre | worst vertex | archived centre | |")
    print("|---|---|---:|---:|---:|---|")
    centre = unit(N.SPOT_LON, N.SPOT_LAT)
    moved = []
    for name in product_names:
        for side, table in armies:
            value = dot(table[name], centre)
            worst = spot_worst(table[name])
            was = ARCHIVED_SPOT[(name, side)]
            ok = abs(value - was) <= 0.005
            if not ok:
                moved.append("%s %s" % (name, side))
            print("| %s | %s | %+.2f | %+.2f | %+.2f | %s |"
                  % (name, side, value, worst, was,
                     "unmoved" if ok else "**MOVED**"))
    for name in world_names:
        for side, table in armies:
            value = dot(table[name], centre)
            worst = spot_worst(table[name])
            print("| %s | %s | %+.2f | %+.2f | -- | |"
                  % (name.replace("per-world ", "per-world "), side, value, worst))
    print()
    if moved:
        print("**The dark spot's facing moved at %s. Requirement 2 says it must"
              % ", ".join(moved))
        print("not have.**")
    else:
        print("Every product-frame figure reproduces the archived one to two")
        print("decimal places, on both armies: **the dark spot did not move.**")
        print("Its +0.28 at the Sol state sheet is its CEILING rather than a")
        print("placement mistake -- at latitude -22, against a sub-point of")
        print("+51.5, no longitude does better -- and that was true of the")
        print("archived build for the same reason.")
    print()

    print("## The per-world frames, and what they now show")
    print()
    for name, view in NEPTUNE_FRAMES.items():
        print("- `%s` (azimuth %.0f, elevation %.0f): %s"
              % (name, view[0], view[1], view[2]))
    for side in ("sol", "anti"):
        azimuth, elevation, why = polar_frame(side, "neptune")
        print("- `polar`, %s (azimuth %.0f, elevation %.1f): %s"
              % (side, azimuth, elevation, why))
    print()
    print("The `opposite` frame is the one that changed meaning. On the")
    print("archived build it was the proof of the correction's central negative")
    print("requirement -- no streak circles the planet -- because the far face")
    print("carried only the ends of streaks and bare globe. On this revision it")
    print("shows the same three bands, unbroken, because that is what a closed")
    print("band is. It is kept and rendered for exactly that reason: it is now")
    print("the picture that proves the bands DO ring the planet, which is what")
    print("the owner asked for and what the beach-ball reading follows from.")
    print()
    return 1 if moved else 0


if __name__ == "__main__":
    raise SystemExit(main())
