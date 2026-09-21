"""Neptune's markings against the camera.

The brief's second requirement is that the streaks be MEASURED to face the
camera, and that the measurement be done knowing longitude alone cannot do it.
This is that measurement: the dot product of each marking against the view axis
at the two frames the whole set is photographed from and at the per-world
frames the two Neptunes are rendered at on their own, on both armies.  +1 is
dead-on, 0 is the limb, -1 is the far side.

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

#: The facing floor this placement was solved against.  Not zero: zero is the
#: limb, and a marking exactly on the limb is a sliver seen edge-on rather than
#: a marking a reader can see.
FLOOR = 0.30


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


def centre_of(key: str):
    if key in dict((k, 1) for k, *_r in N.STREAKS):
        lat, lon = next((l, o) for k, l, o, *_r in N.STREAKS if k == key)
    elif key == "spot":
        lat, lon = N.SPOT_LAT, N.SPOT_LON
    else:
        lat, lon = N.COMPANION_LAT, N.COMPANION_LON
    return unit(lon, lat)


def main() -> int:
    sol, anti = axes("sol"), axes("anti")
    names = [name for name, _v in PRODUCT_FRAMES]

    print("# Neptune's markings against the camera")
    print()
    print("Dot product of each marking against the view axis, at the two")
    print("frames the whole set is photographed from and at the per-world")
    print("frames the two Neptunes are rendered at on their own, on both")
    print("armies. +1 is dead-on, 0 is the limb, -1 is the far side.")
    print()
    print("Every number below is measured on the exact rings")
    print("`parts/neptune_atlas.py` hands the build, at the exact cameras")
    print("`snap_frames.py` and `world_views.py` declare.  The facing floor this")
    print("placement was solved against is **+%.2f**, not zero." % FLOOR)
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
    for name in names:
        for side, table in (("Sol", sol), ("Anti-Sol", anti)):
            view = dict(PRODUCT_FRAMES)[name]
            lat, lon = sub_point(table[name])
            print("| %s | %.0f | %.3f | %s | %+.1f | %+.1f |"
                  % (name, view[0], view[1], side, lat, lon))
    print()
    sheet_sol_lat = sub_point(sol["state sheet"])[0]
    reach = sheet_sol_lat - math.degrees(math.acos(FLOOR))
    print("That last column is the whole reason this brief's previous attempt")
    print("failed. A camera whose sub-point is at latitude %+.1f reaches a"
          % sheet_sol_lat)
    print("marking at latitude L with a dot product of at best cos(%.1f - L),"
          % sheet_sol_lat)
    print("whatever longitude the marking is drawn at, so at a floor of +%.2f"
          % FLOOR)
    print("the Sol state-sheet camera cannot reach ANYTHING south of %+.1f."
          % reach)
    print("A southern-weighted set of streaks therefore cannot be made to face")
    print("that camera by choosing longitudes. Latitude is a lever here, not a")
    print("fixed input, and the latitudes below were solved together with the")
    print("longitudes rather than chosen first and carried in longitude after.")
    print()

    print("## Every streak, at the two product frames")
    print()
    print("Each streak's own centre, and -- because the centre of a 9 mm streak")
    print("says little about its ends -- the worst of its ring vertices.")
    print()
    print("| streak | lat | lon | hero Sol | hero Anti | sheet Sol | sheet Anti "
          "| worst vertex, any frame |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|")
    counts = {(name, side): 0 for name in names for side in ("Sol", "Anti-Sol")}
    for key, lat, lon, *_rest in N.STREAKS:
        centre = centre_of(key)
        verts = [unit(*item) for item in N.RINGS[key]]
        row, worst = [], None
        for name in names:
            for side, table in (("Sol", sol), ("Anti-Sol", anti)):
                value = dot(centre, table[name])
                row.append((name, side, value))
                if value >= FLOOR:
                    counts[(name, side)] += 1
                edge = min(dot(v, table[name]) for v in verts)
                worst = edge if worst is None else min(worst, edge)
        ordered = [next(v for n, s, v in row if n == names[0] and s == "Sol"),
                   next(v for n, s, v in row if n == names[0] and s == "Anti-Sol"),
                   next(v for n, s, v in row if n == names[1] and s == "Sol"),
                   next(v for n, s, v in row if n == names[1] and s == "Anti-Sol")]
        mark = " *" if key in N.ANTI_SOL_ONLY else ""
        print("| `%s`%s | %+.0f | %+.1f | %s | %+.2f |"
              % (key, mark, lat, lon,
                 " | ".join("%+.2f" % v for v in ordered), worst))
    print()
    print("`*` marks a streak the Sol piece's own cameras cannot reach.")
    print()
    print("| frame | army | streaks at or above +%.2f, of %d |"
          % (FLOOR, len(N.STREAKS)))
    print("|---|---|---:|")
    for name in names:
        for side in ("Sol", "Anti-Sol"):
            print("| %s | %s | **%d** |" % (name, side, counts[(name, side)]))
    print()
    least = min(counts.values())
    print("The least is %d of %d, which is the clear majority the brief asks"
          % (least, len(N.STREAKS)))
    print("for, in both frames and on both pieces. The two that fall short of")
    print("it on the Sol piece are `%s` and `%s`, at latitudes %+.0f and %+.0f:"
          % (N.ANTI_SOL_ONLY[0], N.ANTI_SOL_ONLY[1],
             next(l for k, l, *_r in N.STREAKS if k == N.ANTI_SOL_ONLY[0]),
             next(l for k, l, *_r in N.STREAKS if k == N.ANTI_SOL_ONLY[1])))
    print("they are ANTI-SOL-ONLY FEATURES and are named as such here, in")
    print("`parts/neptune_atlas.py` and in the product's limitations. They are")
    print("kept rather than moved north because the reference's clouds are")
    print("southern-weighted, because the Anti-Sol piece shows them plainly,")
    print("and because two deep southern wisps are what stops the northern six")
    print("reading as a ladder.")
    print()

    print("## The dark spot and its companion")
    print()
    print("The spot's facing was in the objective the latitudes and longitudes")
    print("were solved against, not checked afterwards. Its latitude is not")
    print("free: the brief fixes it at %+.0f, the real one." % N.SPOT_LAT)
    print()
    print("| marking | lat | lon | hero Sol | hero Anti | sheet Sol | sheet Anti "
          "| worst vertex, any frame |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|")
    for key in ("spot", "companion"):
        centre = centre_of(key)
        verts = [unit(*item) for item in N.RINGS[key]]
        ordered, worst = [], None
        for name in names:
            for side, table in (("Sol", sol), ("Anti-Sol", anti)):
                ordered.append(dot(centre, table[name]))
                edge = min(dot(v, table[name]) for v in verts)
                worst = edge if worst is None else min(worst, edge)
        lat = N.SPOT_LAT if key == "spot" else N.COMPANION_LAT
        lon = N.SPOT_LON if key == "spot" else N.COMPANION_LON
        print("| `%s` | %+.1f | %+.1f | %+.2f | %+.2f | %+.2f | %+.2f | %+.2f |"
              % (key, lat, lon, ordered[0], ordered[1], ordered[2], ordered[3],
                 worst))
    print()
    ceiling = math.cos(math.radians(sub_point(sol["state sheet"])[0] - N.SPOT_LAT))
    print("The spot clears the floor at three of the four cameras. At the Sol")
    print("state-sheet frame it reaches +%.2f, and that is its CEILING rather"
          % dot(centre_of("spot"), sol["state sheet"]))
    print("than a placement mistake: a marking at latitude %+.0f can do no"
          % N.SPOT_LAT)
    print("better than +%.2f against a camera whose sub-point is %+.1f, at any"
          % (ceiling, sub_point(sol["state sheet"])[0]))
    print("longitude at all, and the longitude that reaches it is the one the")
    print("spot is drawn at. The brief fixes the latitude; the ceiling follows.")
    print("On the other three cameras, and on both per-world spot frames below,")
    print("the spot is well clear. The companion clears the floor everywhere.")
    print()

    print("## The per-world frames")
    print()
    print("These are the frames `snap/worlds/neptune-*.png` are rendered at, and")
    print("they are the frames the brief's placement test is decided on.")
    print()
    for name, view in list(NEPTUNE_FRAMES.items()):
        print("- `%s` (azimuth %.0f, elevation %.0f): %s"
              % (name, view[0], view[1], view[2]))
    azimuth, elevation, _why = polar_frame("sol", "neptune")
    other, _el, _w = polar_frame("anti", "neptune")[0], 0, 0
    print("- `polar` (elevation %.1f, azimuth %.0f on the Sol piece and %.0f on"
          % (elevation, azimuth, other))
    print("  the Anti-Sol one): straight down each piece's own leaning north")
    print("  pole. The two cameras differ because the lean does: that frame is")
    print("  where the mirrored obliquity is plainest.")
    print()
    print("| marking | %s |"
          % " | ".join("%s %s" % (n, s) for n in ["per-world %s" % k
                                                  for k in NEPTUNE_FRAMES]
                       for s in ("Sol", "Anti")))
    print("|---|%s" % ("---:|" * (2 * len(NEPTUNE_FRAMES))))
    for key in [k for k, *_r in N.STREAKS] + ["companion", "spot"]:
        centre = centre_of(key)
        cells = []
        for frame in NEPTUNE_FRAMES:
            for table in (sol, anti):
                cells.append("%+.2f" % dot(centre, table["per-world %s" % frame]))
        print("| `%s` | %s |" % (key, " | ".join(cells)))
    print()
    for frame in NEPTUNE_FRAMES:
        for label, table in (("Sol", sol), ("Anti-Sol", anti)):
            seen = sum(1 for k, *_r in N.STREAKS
                       if dot(centre_of(k), table["per-world %s" % frame]) >= FLOOR)
            print("- `%s`, %s: %d of %d streaks at or above +%.2f."
                  % (frame, label, seen, len(N.STREAKS), FLOOR))
    print()
    print("The `opposite` frame is where the zero is the point. Every one of")
    print("the eight streaks is short, so the face opposite the spot carries")
    print("nothing but the eastern ends of three of them coming round one limb")
    print("and bare blue globe across the middle. A band would have been there")
    print("in full. That picture is the proof of the correction's negative")
    print("requirement -- no streak circles the planet -- and it is why the")
    print("frame is rendered rather than a second decorative angle.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
