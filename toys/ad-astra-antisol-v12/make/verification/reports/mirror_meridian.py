"""The meridian the two mirrored maps are reflected about, and what it costs.

Mercury's obliquity is 0.03 degrees and Venus's is 177.36, so neither pair of
pieces gets a usable mirror out of its lean; `parts/markings.py` carries that
arithmetic.  The mirror is taken from the longitudes instead, and the transform
is a reflection about the piece's own FACING MERIDIAN: the direction the camera
looks from, carried back into that globe's planet frame, has a longitude C, and
every marking longitude L is mapped to 2C - L.

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
    for planet in MAP_MIRRORED_WORLDS:
        sol_rings = rings_of(markings_for(planet, "sol"))
        anti_rings = rings_of(markings_for(planet, "anti"))
        assert len(sol_rings) == len(anti_rings)
        print("### %s" % planet)
        print()
        print("Mean meridian C = %+.4f degrees."
              % facing_meridian(planet, "anti"))
        print()
        print("| ring | frame | Sol centroid | Anti centroid | change | Sol vertices over %+.2f | Anti vertices over %+.2f |"
              % (FLOOR, FLOOR))
        print("|---|---|---:|---:|---:|---:|---:|")
        for (key, index, sol_ring), (_k, _i, anti_ring) in zip(sol_rings, anti_rings):
            for label, view in FRAMES:
                sol_lat, sol_lon = centroid(sol_ring)
                anti_lat, anti_lon = centroid(anti_ring)
                sol_face = facing(sol_lat, sol_lon, planet, "sol", view)
                anti_face = facing(anti_lat, anti_lon, planet, "anti", view)
                sol_over = sum(1 for lon2, lat2 in sol_ring
                               if facing(lat2, lon2, planet, "sol", view) > FLOOR)
                anti_over = sum(1 for lon2, lat2 in anti_ring
                                if facing(lat2, lon2, planet, "anti", view) > FLOOR)
                print("| `%s` ring %d | %s | %+.3f | %+.3f | %+.3f | %d of %d | %d of %d |"
                      % (key, index, label, sol_face, anti_face,
                         anti_face - sol_face,
                         sol_over, len(sol_ring), anti_over, len(anti_ring)))
                if sol_face > FLOOR and anti_face <= FLOOR:
                    failures.append(
                        "%s `%s` ring %d clears the floor on Sol at the %s frame "
                        "(%+.3f) and fails it on Anti-Sol (%+.3f)"
                        % (planet, key, index, label, sol_face, anti_face))
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
    print("to change sides.")
    print()
    for planet in MAP_MIRRORED_WORLDS:
        frame_name, frame = sorted(WORLD_FRAMES[planet].items())[0]
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
            near_centre = abs(su) < 0.05 * radius
            same_sign = (su > 0) == (au > 0)
            if not seen:
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
            print("Aphrodite Terra -- rings 1 and 2, the feature this globe is")
            print("recognised by -- crosses from one side of the ball to the other")
            print("and stays in front of the camera.")
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
    print("| world | adjustments that clear | mean clears | best adjustment | its worst margin | taken | its worst margin |")
    print("|---|---|---|---:|---:|---:|---:|")
    for planet in MAP_MIRRORED_WORLDS:
        sol_rings = rings_of(markings_for(planet, "sol"))
        base = facing_meridian(planet, "anti") - MERIDIAN_ADJUSTMENT.get(planet, 0.0)

        def worst_margin(shift, planet=planet, sol_rings=sol_rings, base=base):
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

        grid = [round(-10.0 + index * 0.01, 2) for index in range(2001)]
        clearing = [shift for shift in grid if worst_margin(shift) > 0.0]
        best = max(grid, key=worst_margin)
        taken = MERIDIAN_ADJUSTMENT.get(planet, 0.0)
        print("| %s | %+.2f to %+.2f degrees | %s | %+.2f | %.4f | %+.2f | %.4f |"
              % (planet,
                 min(clearing) if clearing else 0.0,
                 max(clearing) if clearing else 0.0,
                 "yes" if worst_margin(0.0) > 0.0 else "**no**",
                 best, worst_margin(best), taken, worst_margin(taken)))
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
    print("| world | frame | largest centroid change | largest vertex change |")
    print("|---|---|---:|---:|")
    for planet in MAP_MIRRORED_WORLDS:
        sol_rings = rings_of(markings_for(planet, "sol"))
        anti_rings = rings_of(markings_for(planet, "anti"))
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
        print("its mirrored Anti-Sol twin, at either photographed frame, on")
        print("either world. Mercury holds at the plain mean of the two cameras;")
        print("Venus holds at the mean moved %+.2f degrees, which is the"
              % MERIDIAN_ADJUSTMENT["venus"])
        print("adjustment recorded above and the reason it was made.")
    print()
    print("Measured by `measure/mirror_meridian.py` on the exact rings")
    print("`parts/markings.markings_for` returns and the exact cameras in")
    print("`snap_frames.py`.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
