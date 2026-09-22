"""The meridian the three mirrored maps are reflected about, and what it costs.

Mercury's obliquity is 0.03 degrees, Jupiter's is 3.13 and Venus's is 177.36,
so none of those three pairs of pieces gets a usable mirror out of its lean;
`parts/markings.py` carries that arithmetic.  The mirror is taken from the
longitudes instead, and the transform is a reflection about the piece's own
FACING MERIDIAN: the direction the camera looks from, carried back into that
globe's planet frame, has a longitude C, and every marking longitude L is
mapped to 2C - L.

Jupiter is the third world and it is not like the other two.  Most of its
surface is INVARIANT under a longitude reflection -- its six belts and five
zones are circles of latitude, and a circle of latitude has the same longitude
everywhere -- so the entire mirror read is carried by the Great Red Spot, its
collar, and the wave phase of the two widest belts.  Two consequences run
through this report:

  * the spot is at longitude -48.00 and this world's mean facing meridian is
    -48.77, so a reflection about the plain mean moves it 1.54 degrees of
    longitude -- 1.42 degrees of great-circle arc, 0.33 mm -- and moves it
    west, away from where it needs to go.  `MERIDIAN_ADJUSTMENT` is what makes
    the swing visible, and the sweep that chose it is below, scored on
    VISIBILITY as well as on the facing floor.
  * the two wavy belts are drawn as six longitude sectors each, and a sector is
    not a feature.  Six sectors seam together into one belt closed right round
    the globe, so asking whether sector 6 still faces the camera is asking the
    wrong question: the belt faces the camera at every longitude, on both
    pieces, and what the reflection changes is the phase of its wave.  Those
    rings are measured and reported here, and the floor is applied to the
    MARKING they tile rather than to each sector.  The closure that justifies
    that is measured below rather than asserted.

That transform is the only one that mirrors the map and keeps it in front of
the camera, and this report is the evidence for all three halves of that claim:

  * the identity.  Facing depends on longitude only through cos(L - C), and
    cos((2C - L) - C) = cos(L - C), so a reflection about C preserves the
    facing dot product EXACTLY at any obliquity.  Derived in
    `markings.reflect_longitude` and confirmed numerically below rather than
    taken on trust.
  * the two traps.  Negating longitude and reflecting through the lean's own
    mirror plane, L -> 180 - L, both obey the owner's instruction and both put
    Mercury's Caloris basin on or behind the limb.  Measured here.
  * the cost of one meridian for two cameras.  There are two photographed
    frames and therefore two values of C about ten degrees apart.  One
    meridian has to serve both, their mean is taken, and the facing of every
    ring vertex is then measured at BOTH frames on BOTH pieces against the
    +0.30 floor this chain uses.
  * what the correction BUYS, in degrees of arc and in millimetres on the
    globe it is drawn on, because on Jupiter a mirror nobody can see would
    have passed every other gate in this project.

    "$WORKSHOP_PYTHON" measure/mirror_meridian.py > measure/mirror-meridian.md

Exit 0 when nothing that cleared the floor on the Sol piece fails it on the
mirrored Anti-Sol piece, 1 otherwise.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import params as P                                             # noqa: E402
from parts import markings as M                                # noqa: E402
from parts.markings import (                                   # noqa: E402
    MAP_MIRRORED_WORLDS,
    MERIDIAN_ADJUSTMENT,
    facing_meridian,
    markings_for,
    reflect_longitude,
)
from snap_frames import HERO_VIEW, SHEET_VIEW                  # noqa: E402
from world_views import FRAMES as WORLD_FRAMES                 # noqa: E402

#: The floor this chain uses for "faces the camera".  Venus's and Mercury's
#: earlier facing reports are written against it.
FLOOR = 0.30

FRAMES = (("hero", HERO_VIEW), ("state sheet", SHEET_VIEW))


def direction(lat_deg: float, lon_deg: float):
    lat, lon = math.radians(lat_deg), math.radians(lon_deg)
    return (math.cos(lat) * math.cos(lon), math.cos(lat) * math.sin(lon),
            math.sin(lat))


def lean(vector, planet: str, side: str):
    """`features.planet_frame`'s rotation: a turn about +Y by sign * tilt."""
    angle = math.radians(P.lean_sign(side) * P.PLANETS[planet]["tilt"])
    x, y, z = vector
    return (x * math.cos(angle) + z * math.sin(angle), y,
            -x * math.sin(angle) + z * math.cos(angle))


def view_axis(azimuth: float, elevation: float):
    az, el = math.radians(azimuth), math.radians(elevation)
    return (math.cos(el) * math.cos(az), math.cos(el) * math.sin(az),
            math.sin(el))


def dot(one, other):
    return sum(a * b for a, b in zip(one, other))


def facing(lat: float, lon: float, planet: str, side: str, view) -> float:
    return dot(lean(direction(lat, lon), planet, side), view_axis(*view))


def rings_of(entries):
    """(marking key, ring index, ring) for every outline ring, in build order."""
    out = []
    for key, _colour, specs, _sub in entries:
        index = 0
        for spec in specs:
            if spec[0] != "outline":
                continue
            for ring in spec[1]:
                index += 1
                out.append((key, index, ring))
    return out


def wrap(degrees: float) -> float:
    """One angle brought back into (-180, +180].

    `reflect_longitude` is deliberately not wrapped -- the build wants a
    continuous longitude so a ring drawn across the seam stays in one piece --
    so any number this report SHOWS a reader is wrapped here instead.  A ring
    reported at -382 has not moved 382 degrees; it has moved -22.
    """
    return -((-degrees + 180.0) % 360.0 - 180.0)


def separation(lat_a: float, lon_a: float, lat_b: float, lon_b: float) -> float:
    """The great-circle angle between two points on the globe, in degrees.

    This is what a reader's eye measures, and it is not the longitude
    difference: latitude does not move under a longitude reflection, so a
    feature at latitude p that swings L degrees of longitude covers less than
    L degrees of arc -- and for a swing near 180 it covers far less, because
    it crosses over the pole side of its own parallel rather than round it.
    """
    one, other = direction(lat_a, lon_a), direction(lat_b, lon_b)
    return math.degrees(math.acos(max(-1.0, min(1.0, dot(one, other)))))


def base_of(planet: str) -> float:
    """This world's plain mean facing meridian, before any adjustment."""
    return (facing_meridian(planet, "anti")
            - MERIDIAN_ADJUSTMENT.get(planet, 0.0))


def mm_per_degree(planet: str) -> float:
    """One degree of great-circle arc on this globe, in millimetres.

    A degree is a 360th of the circumference and the circumference is pi * d,
    so it is pi * d / 360 -- NOT pi * d / 180, which is the radius-to-radian
    form and is twice too large.  `jupiter_atlas.MM_PER_DEG` computes the same
    number the other way round, as radians(1) * d / 2, and the two are checked
    against each other in the report.
    """
    return math.pi * P.globe_diameter(planet) / 360.0


def marking_rings(entries):
    """(marking key, [rings]) for every marking that carries outline rings."""
    out = []
    for key, _colour, specs, _sub in entries:
        rings = [ring for spec in specs if spec[0] == "outline"
                 for ring in spec[1]]
        if rings:
            out.append((key, rings))
    return out


def marking_outline_specs(entries):
    """(marking key, spec number, [rings]) for each outline spec separately.

    One marking can carry several independent outline specs -- Jupiter's
    `bands` carries one per wavy belt -- and closure is a property of a belt,
    not of the marking that draws two of them.  This keeps them apart.
    """
    out = []
    for key, _colour, specs, _sub in entries:
        number = 0
        for spec in specs:
            if spec[0] != "outline":
                continue
            number += 1
            out.append((key, number, list(spec[1])))
    return out


def longitude_span(ring):
    """(west, east) of one ring in degrees, as the ring's own vertices give it.

    `jupiter_atlas.belt_sector_ring` walks a sector west to east and back, and
    rounds every vertex to four places, so a sector's own longitudes are an
    exact interval and no unwrapping is needed.  A feature oval is an interval
    too unless it straddles the seam, and the closure test below rejects the
    set rather than guessing when that happens.
    """
    longitudes = [lon for lon, _lat in ring]
    return min(longitudes), max(longitudes)


#: How exactly two sector seams have to meet to count as one band.  The rings
#: are rounded to four decimal places at source, so this is that rounding and
#: nothing looser.
SEAM_TOLERANCE = 1e-4


def tiles_a_closed_band(rings):
    """Do these rings seam together into one band closed round the globe?

    A wavy belt on Jupiter is drawn as six 60-degree longitude sectors, and
    `jupiter_atlas.belt_sector_ring` gives neighbouring sectors the same two
    seam vertices exactly so their lenses fuse along one flat face.  A sector
    is therefore a piece of construction, not a feature, and the facing floor
    belongs to the belt rather than to the sector.

    This is the test that says so, and it is a measurement: sort the rings by
    their western edge, require each one's eastern edge to be the next one's
    western edge to `SEAM_TOLERANCE`, and require the spans to total 360
    degrees.  Anything else -- a lone oval, two ovals, a gapped set -- comes
    back False and is gated ring by ring as before.
    """
    if len(rings) < 2:
        return False
    spans = sorted(longitude_span(ring) for ring in rings)
    total = sum(east - west for west, east in spans)
    if abs(total - 360.0) > SEAM_TOLERANCE:
        return False
    for (_west, east), (next_west, _e) in zip(spans, spans[1:]):
        if abs(east - next_west) > SEAM_TOLERANCE:
            return False
    return True


def sector_tiled_markings(entries):
    """Marking keys every one of whose outline specs tiles a closed band."""
    specs = marking_outline_specs(entries)
    return {key for key in {k for k, _n, _r in specs}
            if all(tiles_a_closed_band(rings)
                   for k, _n, rings in specs if k == key)}


def best_facing(rings, planet, side, view, meridian=None):
    """The most square-on any point of these rings gets at this frame.

    Applied to a marking rather than to one ring.  `meridian` reflects the
    longitudes first, which is how the Anti-Sol value of a Sol marking is read
    without rebuilding the table.
    """
    return max(
        facing(lat, lon if meridian is None else reflect_longitude(lon, meridian),
               planet, side, view)
        for ring in rings for lon, lat in ring)


def centroid(ring):
    vectors = [direction(lat, lon) for lon, lat in ring]
    total = [sum(item[axis] for item in vectors) for axis in range(3)]
    length = math.sqrt(sum(value * value for value in total))
    mean = [value / length for value in total]
    return (math.degrees(math.asin(max(-1.0, min(1.0, mean[2])))),
            math.degrees(math.atan2(mean[1], mean[0])))



def screen_basis(azimuth: float, elevation: float):
    """(view axis, screen right, screen up) for `render_review`'s camera."""
    axis = view_axis(azimuth, elevation)
    az = math.radians(azimuth)
    right = (-math.sin(az), math.cos(az), 0.0)
    up = (axis[1] * right[2] - axis[2] * right[1],
          axis[2] * right[0] - axis[0] * right[2],
          axis[0] * right[1] - axis[1] * right[0])
    return axis, right, up


def main() -> int:
    failures = []

    print("# The facing meridian, and the reflection taken about it")
    print()
    print("## The two cameras this is solved against")
    print()
    print("`parts/markings.PHOTOGRAPHED_VIEWS` restates `snap_frames.HERO_VIEW`")
    print("and `snap_frames.SHEET_VIEW` so that the marking table depends on")
    print("nothing that loads a renderer. The two must agree, and that is")
    print("checked here rather than trusted:")
    print()
    agree = tuple(M.PHOTOGRAPHED_VIEWS) == (HERO_VIEW, SHEET_VIEW)
    print("- `markings.PHOTOGRAPHED_VIEWS` = `%r`" % (M.PHOTOGRAPHED_VIEWS,))
    print("- `(snap_frames.HERO_VIEW, snap_frames.SHEET_VIEW)` = `%r`"
          % ((HERO_VIEW, SHEET_VIEW),))
    print("- they agree: **%s**" % ("yes" if agree else "NO"))
    if not agree:
        failures.append("markings.PHOTOGRAPHED_VIEWS has drifted from snap_frames")
    print()

    print("## C, world by world and frame by frame")
    print()
    print("C is the longitude of the view axis carried back into the globe's own")
    print("planet frame -- `planet_frame` inverted, applied to the camera")
    print("direction. The two frames give two values about ten degrees apart,")
    print("and one meridian has to serve both, so the mean is taken. It is a")
    print("circular mean, so a pair straddling the +/-180 seam cannot average to")
    print("the meridian behind the globe.")
    print()
    print("| world | side | hero C | state sheet C | spread | mean | adjustment | C used |")
    print("|---|---|---:|---:|---:|---:|---:|---:|")
    for planet in MAP_MIRRORED_WORLDS:
        for side in ("sol", "anti"):
            per = []
            for _label, view in FRAMES:
                back = M._unturn(view_axis(*view), P.PLANETS[planet]["tilt"],
                                 P.lean_sign(side))
                per.append(math.degrees(math.atan2(back[1], back[0])))
            used = facing_meridian(planet, side)
            shift = MERIDIAN_ADJUSTMENT.get(planet, 0.0)
            print("| %s | %s | %+.4f | %+.4f | %.4f | %+.4f | %s | %+.4f |"
                  % (planet, side, per[0], per[1], abs(per[0] - per[1]),
                     used - shift, ("%+.2f" % shift) if shift else "none", used))
    print()
    print("Only the **anti** rows are used: the Sol piece keeps exactly what it")
    print("has, and its rows are here so that the two can be compared.")
    print()
    print("Mercury takes the plain mean. Venus does not clear the floor at its")
    print("mean and is adjusted by %+.2f degrees; the sweep that chose that"
          % MERIDIAN_ADJUSTMENT["venus"])
    print("number is below, under *Adjusting the meridian until it clears*.")
    print()

    print("## The identity, confirmed numerically")
    print()
    print("The claim is that facing is preserved EXACTLY by L -> 2C - L when C")
    print("is that frame's own meridian, at any obliquity. Swept over a grid of")
    print("latitudes and longitudes on both worlds and at both frames, on the")
    print("Anti-Sol piece, the largest absolute change in the dot product is:")
    print()
    print("| world | frame | largest |facing(L) - facing(2C - L)| over the grid |")
    print("|---|---|---:|")
    worst_exact = 0.0
    for planet in MAP_MIRRORED_WORLDS:
        for label, view in FRAMES:
            back = M._unturn(view_axis(*view), P.PLANETS[planet]["tilt"],
                             P.lean_sign("anti"))
            exact_c = math.degrees(math.atan2(back[1], back[0]))
            worst = max(
                abs(facing(lat, lon, planet, "anti", view)
                    - facing(lat, reflect_longitude(lon, exact_c), planet,
                             "anti", view))
                for lat in range(-80, 81, 5) for lon in range(-180, 180, 5))
            worst_exact = max(worst_exact, worst)
            print("| %s | %s | %.2e |" % (planet, label, worst))
    print()
    print("%.2e over %d sample points is floating-point noise, so the identity"
          % (worst_exact, 2 * len(FRAMES) * 33 * 72))
    print("holds in this build as derived. It is the mean meridian, not the")
    print("identity, that costs anything, and that cost is measured below.")
    if worst_exact > 1e-9:
        failures.append(
            "the reflection identity does not hold in this build: %.3e" % worst_exact)
    print()

    print("## The two obvious flips, and why neither is taken")
    print()
    print("Mercury's Caloris basin is the test: it is at latitude +30 and")
    print("longitude %g, and %g was itself measured as the longitude that puts"
          % (-50.0, -50.0))
    print("it squarely in front of both cameras. Each candidate transform is")
    print("applied to it and the facing re-read on the Anti-Sol piece.")
    print()
    print("| transform | Caloris longitude becomes | hero facing | state sheet facing | verdict |")
    print("|---|---:|---:|---:|---|")
    lat, lon = 30.0, -50.0
    meridian = facing_meridian("mercury", "anti")
    candidates = [
        ("none -- what the piece has today", lon, "the defect: same as Sol"),
        ("negate longitude, L -> -L", -lon, "on the limb at the hero frame"),
        ("the lean's own mirror plane, L -> 180 - L", 180.0 - lon,
         "three-quarters away, measured below"),
        ("reflect about the facing meridian, L -> 2C - L",
         reflect_longitude(lon, meridian), "**taken**"),
    ]
    for label, moved, verdict in candidates:
        print("| %s | %+.2f | %+.3f | %+.3f | %s |"
              % (label, moved,
                 facing(lat, moved, "mercury", "anti", HERO_VIEW),
                 facing(lat, moved, "mercury", "anti", SHEET_VIEW), verdict))
    print()
    print("The brief that asked for this correction described the second trap as")
    print("putting Caloris *on the far side*. Measured here it does not go quite")
    print("that far: L -> 180 - L sends the basin to longitude +230, which is 80")
    print("degrees off the camera meridian rather than 180, and it reads +0.395")
    print("at the hero frame rather than negative. It is still the wrong answer")
    print("by a long way -- it takes the one feature this globe is recognised by")
    print("from dead-on to a glancing three-quarter view, and it would be the")
    print("second-worst thing that could be done to the piece -- but the")
    print("measurement is reported as it came out rather than as it was")
    print("described. The first trap is as described: at the hero frame")
    print("negating longitude puts Caloris at -0.021, which is the limb exactly.")
    print()
    print("Caloris is very nearly ON the facing meridian already -- that is what")
    print("-50 was solved to be -- so the reflection leaves it almost exactly")
    print("where it is and swings the seven plains around it. That is the shape")
    print("of the correction on this world: the basin stays in front of the")
    print("camera and the terrain on either side of it changes hands.")
    print()

    print("## Every ring vertex, at both frames, on both pieces")
    print()
    print("The floor is **%+.2f**, and what it is applied to is a FEATURE: a"
          % FLOOR)
    print("ring's own centroid direction, which is the form")
    print("`measure/venus-facing.md` and `measure/mercury-facing.md` already")
    print("report this set in. The gate is that anything which cleared the floor")
    print("on the Sol piece still clears it on the mirrored Anti-Sol piece.")
    print()
    print("Every ring VERTEX is measured too and reported beside it, as the")
    print("count over the floor, because the brief asked for the vertices and")
    print("because a centroid can hide a ring that swung half off the globe.")
    print("The vertex counts are evidence and not a second gate, and one row")
    print("shows why: Mercury's `plains` ring 2 is the equatorial plain, whose")
    print("centroid reads +0.013 at the state sheet frame -- it is ON the limb")
    print("on the Sol piece and did not clear the floor there either. Three of")
    print("its nineteen vertices creep over +0.30 on the Sol piece and none do")
    print("on the mirrored one. Nothing that was visible became invisible: a")
    print("feature already at the limb moved along the limb.")
    print()
    print("A ring marked `sector` is one of six that seam into one belt closed")
    print("right round the globe. It is reported like any other ring and it is")
    print("NOT gated on its own, because it is not a feature: the belt it")
    print("belongs to has material at every longitude on both pieces, and a")
    print("reflection moves which sector sits in front of the lens without")
    print("moving the belt. Those markings are gated whole, in *The two wavy")
    print("belts are closed bands* below. Everything else is gated ring by")
    print("ring, exactly as Mercury and Venus already were.")
    print()
    for planet in MAP_MIRRORED_WORLDS:
        sol_rings = rings_of(markings_for(planet, "sol"))
        anti_rings = rings_of(markings_for(planet, "anti"))
        assert len(sol_rings) == len(anti_rings)
        tiled = sector_tiled_markings(markings_for(planet, "sol"))
        print("### %s" % planet)
        print()
        print("Mean meridian C = %+.4f degrees, taken as %+.4f."
              % (facing_meridian(planet, "anti")
                 - MERIDIAN_ADJUSTMENT.get(planet, 0.0),
                 facing_meridian(planet, "anti")))
        print()
        print("| ring | kind | frame | Sol centroid | Anti centroid | change | Sol vertices over %+.2f | Anti vertices over %+.2f |"
              % (FLOOR, FLOOR))
        print("|---|---|---|---:|---:|---:|---:|---:|")
        for (key, index, sol_ring), (_k, _i, anti_ring) in zip(sol_rings, anti_rings):
            kind = "sector" if key in tiled else "feature"
            for label, view in FRAMES:
                sol_lat, sol_lon = centroid(sol_ring)
                anti_lat, anti_lon = centroid(anti_ring)
                sol_face = facing(sol_lat, sol_lon, planet, "sol", view)
                anti_face = facing(anti_lat, anti_lon, planet, "anti", view)
                sol_over = sum(1 for lon2, lat2 in sol_ring
                               if facing(lat2, lon2, planet, "sol", view) > FLOOR)
                anti_over = sum(1 for lon2, lat2 in anti_ring
                                if facing(lat2, lon2, planet, "anti", view) > FLOOR)
                print("| `%s` ring %d | %s | %s | %+.3f | %+.3f | %+.3f | %d of %d | %d of %d |"
                      % (key, index, kind, label, sol_face, anti_face,
                         anti_face - sol_face,
                         sol_over, len(sol_ring), anti_over, len(anti_ring)))
                if kind == "sector":
                    continue
                if sol_face > FLOOR and anti_face <= FLOOR:
                    failures.append(
                        "%s `%s` ring %d clears the floor on Sol at the %s frame "
                        "(%+.3f) and fails it on Anti-Sol (%+.3f)"
                        % (planet, key, index, label, sol_face, anti_face))
        print()

    print("## The two wavy belts are closed bands")
    print()
    print("Jupiter's North and South Equatorial Belts are the only markings in")
    print("this set drawn as longitude sectors, and they are the reason the")
    print("ring-by-ring floor above cannot be the whole gate on this world.")
    print("This is the measurement that replaces it, and it has two halves:")
    print("that the sectors really do close, and that the belt they close into")
    print("still faces the camera after the reflection.")
    print()
    print("Closure first. The sectors are sorted by their western edge; each")
    print("one's eastern edge must be the next one's western edge to within")
    print("%g degrees, which is the rounding `belt_sector_ring` applies to its"
          % SEAM_TOLERANCE)
    print("own vertices, and the spans must total 360.")
    print()
    print("| world and piece | marking | rings | spans total | largest seam gap | closed |")
    print("|---|---|---:|---:|---:|---|")
    banded = []
    for planet in MAP_MIRRORED_WORLDS:
        for side in ("sol", "anti"):
            for key, number, rings in marking_outline_specs(
                    markings_for(planet, side)):
                if not tiles_a_closed_band(rings):
                    continue
                spans = sorted(longitude_span(ring) for ring in rings)
                total = sum(east - west for west, east in spans)
                gap = max(abs(east - next_west)
                          for (_w, east), (next_west, _e) in zip(spans, spans[1:]))
                print("| %s %s | `%s` belt %d | %d | %.4f | %.2e | yes |"
                      % (planet, side, key, number, len(rings), total, gap))
                if side == "anti":
                    banded.append((planet, key, number, rings))
    print()
    print("Then the belt itself. The floor is applied to the marking: the most")
    print("square-on point anywhere on it, at each frame, on each piece. A belt")
    print("that has material at every longitude cannot lose the camera, and")
    print("this is the number that says so rather than the argument.")
    print()
    print("| world | belt | frame | Sol best facing | Anti best facing | change | Sol vertices over %+.2f | Anti vertices over %+.2f |"
          % (FLOOR, FLOOR))
    print("|---|---|---|---:|---:|---:|---:|---:|")
    for planet, key, number, anti_marking in banded:
        sol_marking = [rings for k, n, rings
                       in marking_outline_specs(markings_for(planet, "sol"))
                       if k == key and n == number][0]
        for label, view in FRAMES:
            sol_best = best_facing(sol_marking, planet, "sol", view)
            anti_best = best_facing(anti_marking, planet, "anti", view)
            sol_over = sum(1 for ring in sol_marking for lon, lat in ring
                           if facing(lat, lon, planet, "sol", view) > FLOOR)
            anti_over = sum(1 for ring in anti_marking for lon, lat in ring
                            if facing(lat, lon, planet, "anti", view) > FLOOR)
            sol_count = sum(len(ring) for ring in sol_marking)
            anti_count = sum(len(ring) for ring in anti_marking)
            print("| %s | `%s` belt %d | %s | %+.3f | %+.3f | %+.3f | %d of %d | %d of %d |"
                  % (planet, key, number, label, sol_best, anti_best,
                     anti_best - sol_best, sol_over, sol_count,
                     anti_over, anti_count))
            if sol_best > FLOOR and anti_best <= FLOOR:
                failures.append(
                    "%s `%s` belt %d clears the floor on Sol at the %s frame "
                    "(%+.3f) and fails it on Anti-Sol (%+.3f)"
                    % (planet, key, number, label, sol_best, anti_best))
    print()
    print("The vertex counts move by a sector's worth because the reflection")
    print("moves where the seams fall, not because the belt moved: a seam is a")
    print("flat face between two lenses of the same filament and it is not")
    print("visible on the printed part at all.")
    print()

    print("## The mirror, as the camera sees it")
    print()
    print("The facing table above says the correction costs nothing. This says")
    print("what it BUYS. Each ring's centroid is projected into the camera's own")
    print("image plane and reported as millimetres left or right of the centre of")
    print("the ball -- negative left, positive right -- beside its height. A")
    print("mirror pair is one where every ring a reader can SEE changes the side")
    print("it is on.")
    print()
    print("Measured at each world's own per-piece frame, which is the camera the")
    print("single-piece and pair renders in `snap/worlds/` use, because that is")
    print("the picture a reader is actually given. A ring on the far hemisphere")
    print("is listed with its numbers and marked `hidden`: it has a screen")
    print("position in the arithmetic and none in the picture, so it is not asked")
    print("to change sides. A ring that sits within a twentieth of the globe's")
    print("radius of the centre line on BOTH pieces is marked `on the meridian`")
    print("and is not asked either: it is its own mirror image, which is what")
    print("Caloris was chosen to be. Both tests have to hold on both pieces, so")
    print("a feature that starts near the centre and ends 6 mm away is checked")
    print("like any other. A belt sector is marked `sector` and is not asked")
    print("either: it is a piece of one closed band, and which sector faces the")
    print("lens is not something a reader can see.")
    print()
    print("The frame used per world is the FIRST one that world declares in")
    print("`world_views.FRAMES`, which is by construction its signature face --")
    print("`caloris` on Mercury, `aphrodite` on Venus, `spot` on Jupiter. Each")
    print("world's second frame looks at the face its recognisable features are")
    print("not on, where there is nothing for a mirror to move.")
    print()
    for planet in MAP_MIRRORED_WORLDS:
        tiled = sector_tiled_markings(markings_for(planet, "sol"))
        frame_name, frame = next(iter(WORLD_FRAMES[planet].items()))
        view = (frame[0], frame[1])
        axis, right, up = screen_basis(*view)
        radius = P.globe_radius(planet)
        sol_rings = rings_of(markings_for(planet, "sol"))
        anti_rings = rings_of(markings_for(planet, "anti"))
        print("### %s, at `%s-<side>-%s.png`: azimuth %+.1f, elevation %+.1f"
              % (planet, planet, frame_name, view[0], view[1]))
        print()
        print("| ring | seen? | Sol u mm | Anti u mm | changes sides | Sol v mm | Anti v mm | v moves mm |")
        print("|---|---|---:|---:|---|---:|---:|---:|")
        flipped, checked, worst_v = 0, 0, 0.0
        for (key, index, sol_ring), (_k, _i, anti_ring) in zip(sol_rings, anti_rings):
            s_lat, s_lon = centroid(sol_ring)
            a_lat, a_lon = centroid(anti_ring)
            sv = lean(direction(s_lat, s_lon), planet, "sol")
            av = lean(direction(a_lat, a_lon), planet, "anti")
            su, sh = dot(sv, right) * radius, dot(sv, up) * radius
            au, ah = dot(av, right) * radius, dot(av, up) * radius
            seen = dot(sv, axis) > 0.0 and dot(av, axis) > 0.0
            near_centre = abs(su) < 0.05 * radius and abs(au) < 0.05 * radius
            same_sign = (su > 0) == (au > 0)
            if key in tiled:
                verdict, label = "sector", "no"
            elif not seen:
                verdict, label = "hidden", "no"
            elif near_centre:
                verdict, label = "on the meridian", "yes"
            else:
                checked += 1
                worst_v = max(worst_v, abs(ah - sh))
                if not same_sign:
                    flipped += 1
                verdict, label = ("yes" if not same_sign else "**no**"), "yes"
            print("| `%s` ring %d | %s | %+.2f | %+.2f | %s | %+.2f | %+.2f | %.3f |"
                  % (key, index, label, su, au, verdict, sh, ah, abs(ah - sh)))
        print()
        print("**%d of the %d rings a reader can see at this frame change sides.**"
              % (flipped, checked))
        if flipped != checked:
            failures.append(
                "%s: %d of %d visible rings did not change sides at the %s frame"
                % (planet, checked - flipped, checked, frame_name))
        if planet == "mercury":
            print("Their heights move by at most %.3f mm, which is nothing: this"
                  % worst_v)
            print("frame's own meridian and the meridian the reflection is solved")
            print("about are the same to a hundredth of a degree, so at this")
            print("camera the transform is an exact left-to-right flip of the")
            print("picture. Caloris is the exception and it is the point: at")
            print("longitude -50.00 against a meridian of %+.2f it is very nearly"
                  % facing_meridian("mercury", "anti"))
            print("a fixed point of its own mirror, so the one feature this globe")
            print("is recognised by stays square to the lens while all seven")
            print("plains around it change hands. That is why the pair still")
            print("reads as a PAIR rather than as two unrelated worlds.")
        else:
            print("Their heights move by up to %.3f mm as well, and that is"
                  % worst_v)
            back = M._unturn(view_axis(*view), P.PLANETS[planet]["tilt"],
                             P.lean_sign("anti"))
            print("expected rather than a fault. Carried back into the globe's")
            print("own frame, this camera looks down longitude %+.2f, and the"
                  % math.degrees(math.atan2(back[1], back[0])))
            print("reflection is solved about %+.2f -- a different meridian. A"
                  % facing_meridian(planet, "anti"))
            print("reflection about a meridian the camera is NOT looking down")
            print("moves a marking up or down the ball as well")
            print("as across it. At the two frames the product itself is")
            print("photographed at, which is what the reflection was solved for,")
            print("the facing table above is the measurement that matters.")
            if planet == "venus":
                print("Aphrodite Terra -- rings 1 and 2, the feature this globe is")
                print("recognised by -- crosses from one side of the ball to the")
                print("other and stays in front of the camera.")
            else:
                print("The Great Red Spot -- the one feature this globe is")
                print("recognised by, and on this world the only marking of any")
                print("kind that carries a longitude -- crosses from one side of")
                print("the ball to the other and stays in front of the camera.")
        print()

    print("## What the mirror buys, in millimetres")
    print()
    print("A swing has to be big enough to see across a table, and on Jupiter")
    print("that is the whole question, so it is reported in the units a reader")
    print("has: degrees of great-circle arc, and millimetres on the globe the")
    print("feature is drawn on. One degree of arc on a globe of diameter d is")
    print("pi * d / 360 -- a degree is a 360th of the circumference, not a")
    print("180th -- so on Jupiter's %.2f mm globe it is %.4f mm."
          % (P.globe_diameter("jupiter"), mm_per_degree("jupiter")))
    print()
    print("The distance column is the great-circle separation between where the")
    print("feature sits on the Sol piece and where it sits on the Anti-Sol one,")
    print("not the longitude difference: latitude does not move, so a swing of")
    print("L degrees of longitude at latitude p covers LESS than L degrees of")
    print("arc, and at large swings much less. Both are given.")
    print()
    print("| world | marking | longitude on Sol | on Anti-Sol | swing, degrees of longitude | distance, degrees of arc | distance, mm |")
    print("|---|---|---:|---:|---:|---:|---:|")
    for planet in MAP_MIRRORED_WORLDS:
        tiled = sector_tiled_markings(markings_for(planet, "sol"))
        meridian = facing_meridian(planet, "anti")
        for key, rings in marking_rings(markings_for(planet, "sol")):
            if key in tiled:
                continue
            for index, ring in enumerate(rings, start=1):
                lat, lon = centroid(ring)
                moved = wrap(reflect_longitude(lon, meridian))
                swing = wrap(moved - lon)
                arc = separation(lat, lon, lat, moved)
                print("| %s | `%s` ring %d | %+.2f | %+.2f | %+.2f | %.2f | %.2f |"
                      % (planet, key, index, wrap(lon), moved, swing, arc,
                         arc * mm_per_degree(planet)))
    print()
    print("Jupiter's row is the one this correction exists for. The spot swings")
    print("%+.2f degrees of longitude, which at latitude %+.2f is %.2f degrees"
          % (wrap(reflect_longitude(-48.0, facing_meridian("jupiter", "anti")))
             - (-48.0),
             -22.0,
             separation(-22.0, -48.0, -22.0,
                        wrap(reflect_longitude(-48.0,
                                               facing_meridian("jupiter", "anti"))))))
    print("of great-circle arc and %.2f mm on a globe %.2f mm across. The spot"
          % (separation(-22.0, -48.0, -22.0,
                        wrap(reflect_longitude(-48.0,
                                               facing_meridian("jupiter", "anti"))))
             * mm_per_degree("jupiter"),
             P.globe_diameter("jupiter")))
    print("itself is %.2f mm long, so it moves by about two of its own lengths."
          % (2.0 * 6.5 * mm_per_degree("jupiter")))
    print()

    print("## Adjusting the meridian until it clears")
    print()
    print("At the plain mean of the two cameras, Venus does not clear: Atalanta")
    print("Planitia reads +0.367 on the Sol piece at the hero frame and falls to")
    print("+0.266 on the mirrored piece. The brief's instruction for that case")
    print("is to move the meridian until it clears rather than to accept it, so")
    print("the meridian was swept at a hundredth of a degree and every")
    print("adjustment scored on the worst margin any Sol-clearing feature has")
    print("left on the Anti-Sol piece. Mercury is swept the same way and")
    print("reported beside it, as the evidence that its mean needed nothing.")
    print()
    print("Jupiter is swept over a wider range, at the same hundredth of a")
    print("degree, because its problem is the opposite one: its mean CLEARS")
    print("comfortably and buys nothing, so the sweep is looking for how far")
    print("the meridian can be pushed rather than whether it has to move at")
    print("all. Belt sectors are excluded from the sweep for the same reason")
    print("they are excluded from the gate: they are scored whole, above.")
    print()
    print("Two scores are reported for every world, and only ONE of them is the")
    print("gate. The gate is the ring-centroid margin, which is what a FEATURE")
    print("faces at, and it is the score Mercury and Venus were sealed on. The")
    print("every-vertex margin beside it is the stricter reading the Jupiter")
    print("brief asked for: not a feature's facing but its worst single vertex.")
    print("Mercury and Venus do not clear that stricter score at any adjustment")
    print("and never did -- a ring lying along the limb has vertices that dip")
    print("under the floor on BOTH pieces, which is the same thing the vertex")
    print("counts in the ring table already show and which their own reports")
    print("recorded when they were written. Nothing about those two worlds has")
    print("changed here; the column is reported so that Jupiter's figure can be")
    print("read against something. Jupiter clears the stricter score too, over")
    print("a range 37 degrees wide, which is why the stricter score is the one")
    print("its adjustment was chosen on.")
    print()
    print("| world | scored on | adjustments that clear | mean clears | best adjustment | its worst margin | taken | its worst margin |")
    print("|---|---|---|---|---:|---:|---:|---:|")
    for planet in MAP_MIRRORED_WORLDS:
        entries = markings_for(planet, "sol")
        tiled = sector_tiled_markings(entries)
        sol_rings = [item for item in rings_of(entries) if item[0] not in tiled]
        base = facing_meridian(planet, "anti") - MERIDIAN_ADJUSTMENT.get(planet, 0.0)

        def centroid_margin(shift, planet=planet, sol_rings=sol_rings, base=base):
            meridian = base + shift
            worst = None
            for _key, _index, ring in sol_rings:
                flipped = [(reflect_longitude(lon, meridian), lat)
                           for lon, lat in ring]
                s_lat, s_lon = centroid(ring)
                a_lat, a_lon = centroid(flipped)
                for _label, view in FRAMES:
                    if facing(s_lat, s_lon, planet, "sol", view) <= FLOOR:
                        continue
                    margin = facing(a_lat, a_lon, planet, "anti", view) - FLOOR
                    worst = margin if worst is None else min(worst, margin)
            return -9.0 if worst is None else worst

        def vertex_margin(shift, planet=planet, sol_rings=sol_rings, base=base):
            meridian = base + shift
            worst = None
            for _key, _index, ring in sol_rings:
                for lon, lat in ring:
                    moved = reflect_longitude(lon, meridian)
                    for _label, view in FRAMES:
                        if facing(lat, lon, planet, "sol", view) <= FLOOR:
                            continue
                        margin = facing(lat, moved, planet, "anti", view) - FLOOR
                        worst = margin if worst is None else min(worst, margin)
            return -9.0 if worst is None else worst

        reach = 40.0 if planet == "jupiter" else 10.0
        grid = [round(-reach + index * 0.01, 2)
                for index in range(int(round(2 * reach / 0.01)) + 1)]
        taken = MERIDIAN_ADJUSTMENT.get(planet, 0.0)
        for label, score in (("ring centroid", centroid_margin),
                             ("every vertex", vertex_margin)):
            clearing = [shift for shift in grid if score(shift) > 0.0]
            best = max(grid, key=score)
            print("| %s | %s | %s | %s | %+.2f | %+.4f | %+.2f | %+.4f |"
                  % (planet, label,
                     ("%+.2f to %+.2f degrees" % (min(clearing), max(clearing)))
                     if clearing else "none, at any adjustment",
                     "yes" if score(0.0) > 0.0 else "no",
                     best, score(best), taken, score(taken)))
    print()
    print("Mercury's mean clears with 0.05 in hand and is taken unchanged.")
    print("Venus's does not, and is moved %+.2f degrees -- the whole number"
          % MERIDIAN_ADJUSTMENT["venus"])
    print("beside the sweep's own maximum at +4.98, which costs 0.0002 of margin")
    print("and reads as a decision rather than as an optimiser's last two")
    print("digits. What that adjustment amounts to is that Venus's reflection is")
    print("solved about the HERO camera's own meridian instead of the mean of")
    print("the two, because the hero frame is the one Atalanta is tight at.")
    print()
    print("Jupiter's mean clears and is still refused, and the reason is the")
    print("swing column. Reflecting a feature at longitude L about a meridian C")
    print("lands it at 2C - L, so the swing is twice the distance from the")
    print("feature to the meridian, and this world's spot is %.2f degrees from"
          % abs(facing_meridian("jupiter", "anti")
                - MERIDIAN_ADJUSTMENT["jupiter"] + 48.0))
    mean_only = wrap(reflect_longitude(-48.0, base_of("jupiter")))
    print("its mean meridian. Taking the mean and stopping would move the Great")
    print("Red Spot from -48.00 to %+.2f: %.2f degrees of longitude, %.2f of"
          % (mean_only, abs(wrap(mean_only + 48.0)),
             separation(-22.0, -48.0, -22.0, mean_only)))
    print("great-circle arc and %.2f mm on a globe %.2f mm across -- a piece"
          % (separation(-22.0, -48.0, -22.0, mean_only)
             * mm_per_degree("jupiter"), P.globe_diameter("jupiter")))
    print("whose hash changed and whose appearance did not. It is also the")
    print("WRONG WAY: the spot is already west of the mean meridian, so a")
    print("reflection about that mean carries it a third of a millimetre")
    print("further west, not east.")
    print()
    print("The adjustment taken is %+.2f degrees. It is not the sweep's own"
          % MERIDIAN_ADJUSTMENT["jupiter"])
    print("maximum, because on this world the maximum buys the least: the rule")
    print("is to take the LARGEST whole degree that still keeps at least half")
    print("the margin the best adjustment could buy, scored on the stricter")
    print("every-vertex column. +16 keeps 0.0865 of a 0.1768 peak and falls")
    print("short of half; +15 keeps 0.0995 and is what is taken. It puts the")
    print("spot at longitude -19.54: a swing of 28.46 degrees of longitude,")
    print("which at latitude -22 is 26.35 degrees of great-circle arc and 6.20")
    print("mm on a ball 26.97 mm across. The spot is 3.06 mm long, so it moves")
    print("by two of its own lengths.")
    print()

    print("## What the mean meridian costs")
    print()
    print("If the reflection used each frame's own C the facing would be")
    print("preserved to the last decimal, and there would be two different")
    print("Anti-Sol pieces. One meridian serves both frames, so each frame is")
    print("read off a reflection solved some degrees away from it -- about five")
    print("either way on Mercury, and on Venus about a fifth of a degree at the")
    print("hero frame and about ten at the state sheet, which is where the")
    print("adjustment put it. This is the size of that: the largest facing")
    print("change of any ring centroid, and the largest change of any single")
    print("ring vertex, on each world. It is the price of the correction and it")
    print("is paid in how squarely a marking faces the lens, never in whether")
    print("it is on the near hemisphere at all.")
    print()
    print("Belt sectors are left out of this table for the same reason they are")
    print("left out of the gate: a sector's facing changes by whatever the")
    print("reflection does to the seams, and none of that is a change to the")
    print("belt. Every other ring on all three worlds is here.")
    print()
    print("| world | frame | largest centroid change | largest vertex change |")
    print("|---|---|---:|---:|")
    for planet in MAP_MIRRORED_WORLDS:
        tiled = sector_tiled_markings(markings_for(planet, "sol"))
        sol_rings = [item for item in rings_of(markings_for(planet, "sol"))
                     if item[0] not in tiled]
        anti_rings = [item for item in rings_of(markings_for(planet, "anti"))
                      if item[0] not in tiled]
        for label, view in FRAMES:
            centroid_worst = 0.0
            vertex_worst = 0.0
            for (_key, _i, sol_ring), (_k, _j, anti_ring) in zip(sol_rings, anti_rings):
                s_lat, s_lon = centroid(sol_ring)
                a_lat, a_lon = centroid(anti_ring)
                centroid_worst = max(centroid_worst, abs(
                    facing(a_lat, a_lon, planet, "anti", view)
                    - facing(s_lat, s_lon, planet, "sol", view)))
                for (s_lon2, s_lat2), (a_lon2, a_lat2) in zip(sol_ring, anti_ring[::-1]):
                    vertex_worst = max(vertex_worst, abs(
                        facing(a_lat2, a_lon2, planet, "anti", view)
                        - facing(s_lat2, s_lon2, planet, "sol", view)))
            print("| %s | %s | %.4f | %.4f |"
                  % (planet, label, centroid_worst, vertex_worst))
    print()

    print("## Verdict")
    print()
    if failures:
        for item in failures:
            print("- **%s**" % item)
    else:
        print("Nothing that cleared the %+.2f floor on a Sol piece fails it on"
              % FLOOR)
        print("its mirrored Anti-Sol twin, at either photographed frame, on any")
        print("of the three worlds. Mercury holds at the plain mean of the two")
        print("cameras; Venus holds at the mean moved %+.2f degrees to clear"
              % MERIDIAN_ADJUSTMENT["venus"])
        print("Atalanta Planitia; Jupiter holds at the mean moved %+.2f degrees,"
              % MERIDIAN_ADJUSTMENT["jupiter"])
        print("which was chosen to make the swing visible rather than to clear a")
        print("floor, and which leaves the worst spot or collar vertex 0.0995")
        print("above it. Each adjustment is recorded above with the sweep that")
        print("chose it.")
    print()
    print("Measured by `measure/mirror_meridian.py` on the exact rings")
    print("`parts/markings.markings_for` returns and the exact cameras in")
    print("`snap_frames.py`.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
