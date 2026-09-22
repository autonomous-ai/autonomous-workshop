"""Which way every Venus marking points at the two photographed frames.

A marking on the hidden hemisphere is not a marking.  The Mariner-10 cloud Y
this revision deletes had to be carried -135 degrees for exactly that reason,
and Jupiter's Great Red Spot -110; the comments recording both live in
`parts/markings.py`, and `measure/mercury-facing.md` is the same measurement
for Mercury.

Venus's offset is not inherited from any of them.  The cloud Y's -135 was
chosen for a pattern that no longer exists and carries no authority over radar
data, so the number below was measured from scratch by sweeping every whole
degree of offset and reading off the one that puts **Aphrodite Terra** most
squarely in front of the camera.  Aphrodite decides because it is the one
feature on Venus with a silhouette a reader can match against the reference:
it spans more than 150 degrees of longitude and it is what the piece is
recognised by.  The rest of the map follows it rather than the other way
round.

`cad/scripts/render_review` puts the camera on the unit vector

    (cos el cos az, cos el sin az, sin el)

in the piece's own frame, and a world stands on the board under a pure
translation, so that vector is the view axis for every piece on the set.  A
marking's own direction is its latitude and longitude in the planet frame,
carried into the piece by the obliquity: rotated about +Y by the true tilt,
positive on a Sol world and negative on its Anti-Sol mirror.  The dot product
of the two is +1 dead-on, 0 at the limb and -1 on the far side.

Venus's obliquity is 177.36 degrees.  That is what turns this world's map over
and it is not corrected here; it is also why the two armies' LEANS agree
closely, in the way Mercury's 0.03 degrees make its two agree -- both leans are
within a few degrees of a half-turn apart from each other, so the mirrored lean
moves a marking by about five degrees rather than by twice the tilt.  That is
the defect the Antisol Mirror revision corrects, and it corrects it in the map
rather than in the lean: `parts/markings.markings_for` reflects the Anti-Sol
piece's longitudes about its own facing meridian, which this report reads
rather than restates.

    "$WORKSHOP_PYTHON" measure/venus_facing.py > measure/venus-facing.md
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import params as P                                            # noqa: E402
from parts.markings import (                                  # noqa: E402
    MAP_MIRRORED_WORLDS,
    facing_meridian,
    reflect_longitude,
)
from parts import venus_atlas as V                            # noqa: E402
from snap_frames import HERO_VIEW, SHEET_VIEW                 # noqa: E402
from world_views import FRAMES as WORLD_FRAMES, polar_frame   # noqa: E402

PLANET = "venus"
TILT = P.PLANETS[PLANET]["tilt"]

#: The two frames the product is photographed at: `snap/iso.png` and the three
#: panels of `snap/signature.png`.  Both come from `snap_frames.py`, so this
#: report cannot drift away from the images it describes.
FRAMES = (("hero", HERO_VIEW), ("state sheet", SHEET_VIEW))

#: Every province, by the name the atlas gives it.  Aphrodite is listed as the
#: undivided feature: the two build rings are one highland and share one
#: direction.
PROVINCES = [
    ("aphrodite_terra", "highland"),
    ("ishtar_terra", "highland"),
    ("beta_regio", "highland"),
    ("phoebe_regio", "highland"),
    ("alpha_regio", "highland"),
    ("themis_regio", "highland"),
    ("lada_terra", "highland"),
    ("atalanta_planitia", "lowland"),
    ("guinevere_planitia", "lowland"),
    ("lavinia_planitia", "lowland"),
]


def direction(lat_deg: float, lon_deg: float):
    lat, lon = math.radians(lat_deg), math.radians(lon_deg)
    return (math.cos(lat) * math.cos(lon),
            math.cos(lat) * math.sin(lon),
            math.sin(lat))


def norm(vector):
    length = math.sqrt(sum(value * value for value in vector))
    return tuple(value / length for value in vector)


def centroid(ring):
    """(latitude, longitude) of the ring's own mean direction, as drawn."""
    vectors = [direction(lat, lon) for lon, lat in ring]
    mean = norm(tuple(sum(item[axis] for item in vectors) for axis in range(3)))
    return (math.degrees(math.asin(max(-1.0, min(1.0, mean[2])))),
            math.degrees(math.atan2(mean[1], mean[0])) % 360.0)


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


def visible_fraction(name: str, view, side: str) -> float:
    """Fraction of a ring's vertices a reader of that frame can actually see.

    A vertex counts only when it is both on the near hemisphere and north of
    the parallel where the seat collar springs, because everything below that
    parallel is inside the collar whichever way the camera points.
    """
    ring = V.offset(V.RINGS[name])
    axis = view_axis(*view)
    seen = 0
    for lon, lat in ring:
        placed = lean(direction(lat, carried(lon, side)), side)
        if sum(one * other for one, other in zip(placed, axis)) <= 0.15:
            continue
        if math.degrees(math.asin(max(-1.0, min(1.0, placed[2])))) \
                <= P.SEAT_LATITUDE_DEG:
            continue
        seen += 1
    return seen / float(len(ring))


def carried(lon_deg: float, side: str) -> float:
    """The longitude this marking is actually drawn at on that piece.

    Since the mirror correction, the Anti-Sol piece of this world carries its
    map reflected about the piece's own facing meridian: L -> 2C - L. The
    reflection is read from `parts/markings.py` rather than restated, so this
    report cannot describe a piece the build does not make.
    """
    if side != "anti" or PLANET not in MAP_MIRRORED_WORLDS:
        return lon_deg
    return reflect_longitude(lon_deg, facing_meridian(PLANET, side))


def facing(lat_deg: float, lon_deg: float, side: str, view) -> float:
    marking = lean(direction(lat_deg, carried(lon_deg, side)), side)
    axis = view_axis(*view)
    return sum(one * other for one, other in zip(marking, axis))


def aphrodite_worst(offset: float) -> float:
    lat, lon = centroid(V.APHRODITE_TERRA)
    return min(facing(lat, lon + offset, side, view)
               for side in ("sol", "anti") for _label, view in FRAMES)


def aphrodite_vertex_fraction(offset: float) -> float:
    ring = V.APHRODITE_TERRA
    return min(
        sum(1 for lon, lat in ring if facing(lat, lon + offset, side, view) > 0)
        / float(len(ring))
        for side in ("sol", "anti") for _label, view in FRAMES
    )


def main() -> int:
    offset = V.LONGITUDE_OFFSET
    centroids = {name: centroid(V.RINGS[name]) for name, _role in PROVINCES}

    print("# Venus's markings against the camera")
    print()
    print("Dot product of each province's own direction against the view axis,")
    print("at the two frames the product is photographed from, on both armies.")
    print("+1 is dead-on, 0 is the limb, -1 is the far side.")
    print()
    print("Every longitude below carries `venus_atlas.LONGITUDE_OFFSET`,")
    print("**%+.0f degrees**, applied to the whole marking set at once."
          % offset)
    print()
    print("**And since the Antisol Mirror revision the Anti-Sol piece carries")
    print("them MIRRORED.** Venus's obliquity is %.2f degrees, so its two"
          % TILT)
    print("pieces differ by 5.28 degrees of lean -- the same turn measured each")
    print("way round -- and the pair showed the same face twice. The Anti-Sol")
    print("piece now reflects every marking longitude about that piece's own")
    print("facing meridian at %+.2f degrees. The `longitude` column below is"
          % facing_meridian(PLANET, "anti"))
    print("the SOL piece's; the Anti-Sol longitude is beside it, and the two")
    print("facing columns are read off the piece each one is actually built as.")
    print("`measure/mirror-meridian.md` is the whole transform, the sweep that")
    print("chose that meridian, and the per-ring table at both frames.")
    print()

    print("## The offset was measured, not inherited")
    print()
    print("The deleted cloud Y carried -135 degrees. That number was chosen for")
    print("a pattern that no longer exists and has no authority over radar")
    print("data, so it was discarded and every whole degree swept instead. The")
    print("criterion is Aphrodite Terra's worst facing across both frames and")
    print("both armies, because Aphrodite is the feature this piece is")
    print("recognised by.")
    print()
    print("| offset | Aphrodite, worst of the four cases | Aphrodite vertices on the near hemisphere, worst case |")
    print("|---:|---:|---:|")
    best = max(range(-179, 181), key=aphrodite_worst)
    for candidate in sorted({-135, 0, best - 30, best, best + 30, 180}):
        mark = " **chosen**" if candidate == best else ""
        print("| %+d%s | %+.3f | %.0f%% |"
              % (candidate, mark, aphrodite_worst(float(candidate)),
                 100.0 * aphrodite_vertex_fraction(float(candidate))))
    print()
    print("The sweep's maximum is %+d degrees and it is the offset the atlas"
          % best)
    print("carries. At it every one of Aphrodite's %d vertices is on the near"
          % len(V.APHRODITE_TERRA))
    print("hemisphere in all four cases, so the whole silhouette is presented")
    print("rather than a piece of it, and the worst of the four centroid")
    print("readings is %+.3f. The old -135 measures %+.3f on the same test,"
          % (aphrodite_worst(offset), aphrodite_worst(-135.0)))
    print("which is why it was not inherited.")
    print()

    for label, view in FRAMES:
        print("## The %s frame: azimuth %g, elevation %g"
              % (label, view[0], view[1]))
        print()
        print("| province | tone | latitude | Sol longitude | Anti-Sol longitude | Sol | Anti-Sol | faces the camera |")
        print("|---|---|---:|---:|---:|---:|---:|---|")
        for name, role in PROVINCES:
            lat, lon = centroids[name]
            sol = facing(lat, lon + offset, "sol", view)
            anti = facing(lat, lon + offset, "anti", view)
            print("| `%s` | %s | %+.1f | %.1f | %.1f | %+.2f | %+.2f | %s |"
                  % (name, role, lat, (lon + offset) % 360.0,
                     carried(lon + offset, "anti") % 360.0, sol, anti,
                     "yes" if min(sol, anti) > 0 else "no"))
        print()

    print("## The single-piece frames")
    print()
    print("`snap/worlds/` renders each Venus piece alone at the two azimuths")
    print("below, measured the same way: the azimuth that puts the named")
    print("province most squarely in front of the camera on both armies at 12")
    print("degrees of elevation. Venus is upside down, so an azimuth is not a")
    print("Venusian longitude here -- the obliquity turns the map over before")
    print("the camera sees it, which is why both were swept rather than read")
    print("off the atlas.")
    print()
    print("| frame | azimuth | elevation | what it is aimed at | Sol | Anti-Sol |")
    print("|---|---:|---:|---|---:|---:|")
    aimed = {"aphrodite": ["aphrodite_terra"],
             "beta_phoebe": ["beta_regio", "phoebe_regio"]}
    for name, (azimuth, elevation, _why) in WORLD_FRAMES[PLANET].items():
        for target in aimed[name]:
            lat, lon = centroids[target]
            print("| `venus-<side>-%s.png` | %+.1f | %+.1f | `%s` | %+.2f | %+.2f |"
                  % (name, azimuth, elevation, target,
                     facing(lat, lon + offset, "sol", (azimuth, elevation)),
                     facing(lat, lon + offset, "anti", (azimuth, elevation))))
    lat, lon = centroids["aphrodite_terra"]
    azimuth, elevation, _why = WORLD_FRAMES[PLANET]["beta_phoebe"]
    print("| the same frame, checked negatively | %+.1f | %+.1f | `aphrodite_terra` | %+.2f | %+.2f |"
          % (azimuth, elevation,
             facing(lat, lon + offset, "sol", (azimuth, elevation)),
             facing(lat, lon + offset, "anti", (azimuth, elevation))))
    print()
    print("The last row is the check that the second frame really is the far")
    print("face: Aphrodite is behind the globe in it, so nothing in")
    print("`venus-<side>-beta_phoebe.png` is the feature the first frame shows.")
    print()

    print("## Can one camera show Aphrodite and the plains at once?")
    print()
    print("No, and the reason is Venus's own geography rather than a framing")
    print("choice. Aphrodite dominates one hemisphere and the three major")
    print("plains lie largely on the other, so a camera cannot present both.")
    print("This is the sweep that establishes it, and it is recorded because an")
    print("independent reader of the single-piece frames asked for exactly that")
    print("camera and it does not exist.")
    print()
    print("The index below is the fraction of a province's own ring vertices")
    print("that are both on the near hemisphere and above the parallel where")
    print("the seat collar springs -- so it counts what a reader can actually")
    print("see -- taken at the worse of the two armies, at %g degrees of"
          % WORLD_FRAMES[PLANET]["aphrodite"][1])
    print("elevation.")
    print()
    print("| azimuth | Aphrodite | Atalanta | Guinevere | Lavinia | plains total |")
    print("|---:|---:|---:|---:|---:|---:|")
    rows = []
    for azimuth in range(-180, 180, 15):
        view = (float(azimuth), WORLD_FRAMES[PLANET]["aphrodite"][1])
        aphrodite = min(
            0.5 * visible_fraction("aphrodite_west", view, side)
            + 0.5 * visible_fraction("aphrodite_east", view, side)
            for side in ("sol", "anti"))
        plains = [min(visible_fraction(name, view, side)
                      for side in ("sol", "anti")) for name in V.LOWLAND_NAMES]
        rows.append((azimuth, aphrodite, plains))
        print("| %+d | %.2f | %.2f | %.2f | %.2f | %.2f |"
              % (azimuth, aphrodite, plains[0], plains[1], plains[2],
                 sum(plains)))
    best_aphrodite = max(rows, key=lambda row: row[1])
    best_plains = max(rows, key=lambda row: sum(row[2]))
    print()
    print("Where Aphrodite is best presented, at azimuth %+d, it reaches %.2f"
          % (best_aphrodite[0], best_aphrodite[1]))
    print("and the plains reach %.2f between them. Where the plains are best"
          % sum(best_aphrodite[2]))
    print("presented, at azimuth %+d, they reach %.2f and Aphrodite falls to"
          % (best_plains[0], sum(best_plains[2])))
    print("%.2f. There is no azimuth at which both are high." % best_plains[1])
    print()
    print("`venus-<side>-aphrodite.png` is therefore aimed at Aphrodite, which")
    print("is the feature the piece is recognised by, and")
    print("`venus-<side>-beta_phoebe.png` is the frame where the plains read as")
    print("terrain. Neither frame is the whole surface and neither is claimed")
    print("to be.")
    print()
    print("## The poles, and which one the obliquity actually produces")
    print()
    print("Venus's obliquity is %.2f degrees, so its north pole points very"
          % TILT)
    print("nearly straight **down**. The camera that looks down it is therefore")
    print("below the board and sees the underside of the disc; the frame that")
    print("shows this world's visible pole region is the south one. Both are")
    print("rendered, and the north one is kept as the evidence of exactly that.")
    print()
    print("| frame | side | azimuth | elevation | what it sees |")
    print("|---|---|---:|---:|---|")
    for side in ("sol", "anti"):
        for pole in ("north", "south"):
            azimuth, elevation, _why = polar_frame(side, PLANET, pole)
            sees = ("the underside of the disc; no part of the globe"
                    if elevation < 0 else
                    "the globe from above, with the disc as a ring around it")
            suffix = "polar" if pole == "north" else "south-polar"
            print("| `venus-%s-%s.png` | %s | %+.2f | %+.2f | %s |"
                  % (side, suffix, pole, azimuth, elevation, sees))
    print()
    print("Measured by `measure/venus_facing.py` on the exact rings in")
    print("`parts/venus_atlas.py` and the exact cameras in `snap_frames.py`")
    print("and `world_views.py`.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
