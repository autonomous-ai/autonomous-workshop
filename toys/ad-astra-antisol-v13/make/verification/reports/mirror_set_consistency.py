"""Which of the eight worlds carry a mirrored map, and the rule that decides it.

After the Jove correction three of the eight worlds carry a mirrored map on the
Anti-Sol piece and five carry one map at two leans.  That is a fact about the
set rather than about any one world, so it is reported once, here, with the
number the rule is actually applied to in every row.

The rule is one line:

    a world joins `markings.MAP_MIRRORED_WORLDS` when the ANGLE BETWEEN ITS
    TWO PIECES' LEANS is too small to show the mirror.

and the thing to notice is that it is a rule about the LEAN, not about the
world.  `parts/world.py` builds the Sol globe through `planet_frame(tilt, +1)`
and its Anti-Sol twin through `planet_frame(tilt, -1)`, so the two pieces of a
pair differ by a rotation of 2 * tilt about +Y -- or by 360 - 2 * tilt, when
2 * tilt runs past half a turn and the shorter way round is the other one.
That angle is what a reader sees when they hold the two pieces up together, and
when it is a few degrees they see nothing.

    "$WORKSHOP_PYTHON" measure/mirror_set_consistency.py \\
        > measure/mirror-set-consistency.md

Exit 0 when the tuple in the source agrees with the rule applied to the tilts
in `params.PLANETS`, 1 otherwise.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import params as P                                             # noqa: E402
from parts.markings import (                                   # noqa: E402
    MAP_MIRRORED_WORLDS,
    MERIDIAN_ADJUSTMENT,
    facing_meridian,
)

#: Above this many degrees between the two pieces' leans, the lean itself shows
#: the mirror and the map is left alone.  It is not a tuned number and it does
#: not need to be: the set has no world anywhere near it.  The three mirrored
#: worlds sit at 0.06, 5.28 and 6.26 degrees and the five leaned ones at 46.88
#: and above, so any threshold between 7 and 46 sorts this set the same way.
#: 20.00 is the round number in the middle of that gap.
LEAN_ANGLE_FLOOR = 20.00


def pole_axis(tilt_deg: float, sign: float):
    """Where this piece's north pole points: +Z turned about +Y by sign*tilt."""
    angle = math.radians(sign * tilt_deg)
    return (math.sin(angle), 0.0, math.cos(angle))


def lean_angle(tilt_deg: float) -> float:
    """The angle between the two pieces' poles, measured the short way round."""
    one = pole_axis(tilt_deg, +1.0)
    other = pole_axis(tilt_deg, -1.0)
    product = sum(a * b for a, b in zip(one, other))
    return math.degrees(math.acos(max(-1.0, min(1.0, product))))


def main() -> int:
    failures = []
    order = sorted(P.PLANETS, key=lambda name: P.PLANETS[name]["rank"])

    print("# Three worlds mirror the map, five mirror only the lean")
    print()
    print("## The rule")
    print()
    print("A world's two pieces differ by a rotation of 2 * tilt about +Y, or by")
    print("360 - 2 * tilt when that is the shorter way round. That angle is the")
    print("whole of the ownership cue: it is what a reader sees when the two")
    print("pieces stand side by side. When it is large the pair reads as two")
    print("different objects with no help at all. When it is a few degrees the")
    print("pair reads as one object photographed twice, and the mirror has to be")
    print("taken from the only other thing the globe carries -- the longitudes")
    print("its markings are drawn at.")
    print()
    print("**A world joins `markings.MAP_MIRRORED_WORLDS` when the angle between")
    print("its two pieces' leans is too small to show the mirror.** The floor is")
    print("%+.2f degrees and it is not a tuned number: the set is nowhere near"
          % LEAN_ANGLE_FLOOR)
    print("it, as the table shows, so any floor between 7 and 46 sorts these")
    print("eight worlds the same way.")
    print()
    print("Nothing here is written by this report. `params.PLANETS` tilts are")
    print("read and never modified, `params.lean_sign` is read and never")
    print("modified, and `features.planet_frame` is not touched by this")
    print("correction at all. The obliquities are observed facts; the defect the")
    print("Jove correction repairs is CAUSED by one of them, so inventing a lean")
    print("would have been correcting the planet rather than the piece.")
    print()

    print("## All eight worlds")
    print()
    print("| rank | world | obliquity, degrees [observed] | angle between the two pieces' leans | route | meridian adjustment |")
    print("|---:|---|---:|---:|---|---:|")
    for planet in order:
        tilt = P.PLANETS[planet]["tilt"]
        angle = lean_angle(tilt)
        mirrored = planet in MAP_MIRRORED_WORLDS
        route = ("**mirrored map**" if mirrored
                 else "one map at two leans")
        shift = MERIDIAN_ADJUSTMENT.get(planet)
        print("| %d | %s | %.2f | %.2f | %s | %s |"
              % (P.PLANETS[planet]["rank"], planet, tilt, angle, route,
                 ("%+.2f" % shift) if shift is not None
                 else ("the plain mean" if mirrored else "--")))
        if mirrored and angle > LEAN_ANGLE_FLOOR:
            failures.append(
                "%s is in MAP_MIRRORED_WORLDS but its pieces are %.2f degrees "
                "apart, which the lean shows on its own" % (planet, angle))
        if not mirrored and angle <= LEAN_ANGLE_FLOOR:
            failures.append(
                "%s is not in MAP_MIRRORED_WORLDS but its pieces are only "
                "%.2f degrees apart" % (planet, angle))
    print()

    mirrored_angles = sorted(lean_angle(P.PLANETS[p]["tilt"])
                             for p in MAP_MIRRORED_WORLDS)
    leaned_angles = sorted(lean_angle(P.PLANETS[p]["tilt"]) for p in order
                           if p not in MAP_MIRRORED_WORLDS)
    print("The three mirrored worlds are %s degrees apart at the lean."
          % ", ".join("%.2f" % value for value in mirrored_angles))
    print("The five that are not are %s."
          % ", ".join("%.2f" % value for value in leaned_angles))
    print("The largest of the three is %.2f and the smallest of the five is"
          % mirrored_angles[-1])
    print("%.2f, so the gap between the two groups is %.2f degrees wide and the"
          % (leaned_angles[0], leaned_angles[0] - mirrored_angles[-1]))
    print("smallest leaned world is %.1f times the largest mirrored one."
          % (leaned_angles[0] / mirrored_angles[-1]))
    print("**Every one of the five is far from degenerate.**")
    print()

    print("## Why Venus and Uranus are not where a reader expects them")
    print()
    print("Two rows in the table look wrong at a glance and are not.")
    print()
    print("**Venus is mirrored although its obliquity is the largest but one in")
    print("the set.** 177.36 degrees is very nearly a half turn, so its Sol")
    print("piece leans +177.36 and its Anti-Sol piece -177.36 -- and those are")
    print("not 354.72 degrees apart, because that is the long way round. The")
    print("short way is 360 - 2 * 177.36 = %.2f degrees. A world tipped almost"
          % lean_angle(P.PLANETS["venus"]["tilt"]))
    print("exactly upside down looks the same tipped either way.")
    print()
    print("**Uranus is not mirrored although a reader is told its pair is hard")
    print("to tell apart.** Its pieces are %.2f degrees apart, which is the"
          % lean_angle(P.PLANETS["uranus"]["tilt"]))
    print("second largest angle in the set, so the LEAN carries the mirror on")
    print("that world with room to spare. What makes its pair hard to read is")
    print("the surface: `MARKINGS[\"uranus\"]` is empty, the globe is bare cyan")
    print("and the only feature on the piece is the white ring. That is a")
    print("separate question from this one, and this rule does not answer it.")
    print("The distinction matters: the rule is about whether the lean can show")
    print("the mirror, not about how legible any particular pair turns out to")
    print("be.")
    print()

    print("## What each mirrored world's mirror is carried by")
    print()
    print("| world | what carries the mirror | what a longitude reflection does not touch |")
    print("|---|---|---|")
    print("| mercury | seven plains that change hands around a Caloris basin that stays square to the lens | the basin's own longitude, which is within 0.01 degrees of the reflection meridian |")
    print("| venus | Aphrodite Terra and the lowlands crossing the ball | nothing: every Venusian marking is an outline with a longitude |")
    print("| jupiter | the Great Red Spot, its collar, and the wave phase of the two widest belts | six belts and five zones, which are circles of latitude and have the same longitude everywhere |")
    print()
    print("Jupiter's row is why its correction needed a `MERIDIAN_ADJUSTMENT`")
    print("and the other two worlds' rows do not read the same way. On Mercury")
    print("and Venus a reflection moves most of the map. On Jupiter it moves")
    print("almost none of it, because almost none of it carries a longitude at")
    print("all, and the whole read falls on one 3 mm oval.")
    print("`measure/mirror-meridian.md` is the sweep that gave that oval")
    print("something to do; the meridian it settles on is %+.4f, which is the"
          % facing_meridian("jupiter", "anti"))
    print("plain mean moved %+.2f degrees." % MERIDIAN_ADJUSTMENT["jupiter"])
    print()

    print("## Verdict")
    print()
    if failures:
        for item in failures:
            print("- **%s**" % item)
    else:
        print("`markings.MAP_MIRRORED_WORLDS` is %r, and that is exactly the set"
              % (MAP_MIRRORED_WORLDS,))
        print("the rule selects from the tilts in `params.PLANETS`: three worlds")
        print("under the %.2f degree floor and five over it, with no world"
              % LEAN_ANGLE_FLOOR)
        print("within 13 degrees of the floor on either side.")
    print()
    print("Measured by `measure/mirror_set_consistency.py` from")
    print("`params.PLANETS` and `parts.markings.MAP_MIRRORED_WORLDS`.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
