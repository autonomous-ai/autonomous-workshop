# Three worlds mirror the map, five mirror only the lean

## The rule

A world's two pieces differ by a rotation of 2 * tilt about +Y, or by
360 - 2 * tilt when that is the shorter way round. That angle is the
whole of the ownership cue: it is what a reader sees when the two
pieces stand side by side. When it is large the pair reads as two
different objects with no help at all. When it is a few degrees the
pair reads as one object photographed twice, and the mirror has to be
taken from the only other thing the globe carries -- the longitudes
its markings are drawn at.

**A world joins `markings.MAP_MIRRORED_WORLDS` when the angle between
its two pieces' leans is too small to show the mirror.** The floor is
+20.00 degrees and it is not a tuned number: the set is nowhere near
it, as the table shows, so any floor between 7 and 46 sorts these
eight worlds the same way.

Nothing here is written by this report. `params.PLANETS` tilts are
read and never modified, `params.lean_sign` is read and never
modified, and `features.planet_frame` is not touched by this
correction at all. The obliquities are observed facts; the defect the
Jove correction repairs is CAUSED by one of them, so inventing a lean
would have been correcting the planet rather than the piece.

## All eight worlds

| rank | world | obliquity, degrees [observed] | angle between the two pieces' leans | route | meridian adjustment |
|---:|---|---:|---:|---|---:|
| 1 | mercury | 0.03 | 0.06 | **mirrored map** | the plain mean |
| 2 | mars | 25.19 | 50.38 | one map at two leans | -- |
| 3 | venus | 177.36 | 5.28 | **mirrored map** | +5.00 |
| 4 | earth | 23.44 | 46.88 | one map at two leans | -- |
| 5 | neptune | 28.32 | 56.64 | one map at two leans | -- |
| 6 | uranus | 97.77 | 164.46 | one map at two leans | -- |
| 7 | saturn | 26.73 | 53.46 | one map at two leans | -- |
| 8 | jupiter | 3.13 | 6.26 | **mirrored map** | +15.00 |

The three mirrored worlds are 0.06, 5.28, 6.26 degrees apart at the lean.
The five that are not are 46.88, 50.38, 53.46, 56.64, 164.46.
The largest of the three is 6.26 and the smallest of the five is
46.88, so the gap between the two groups is 40.62 degrees wide and the
smallest leaned world is 7.5 times the largest mirrored one.
**Every one of the five is far from degenerate.**

## Why Venus and Uranus are not where a reader expects them

Two rows in the table look wrong at a glance and are not.

**Venus is mirrored although its obliquity is the largest but one in
the set.** 177.36 degrees is very nearly a half turn, so its Sol
piece leans +177.36 and its Anti-Sol piece -177.36 -- and those are
not 354.72 degrees apart, because that is the long way round. The
short way is 360 - 2 * 177.36 = 5.28 degrees. A world tipped almost
exactly upside down looks the same tipped either way.

**Uranus is not mirrored although a reader is told its pair is hard
to tell apart.** Its pieces are 164.46 degrees apart, which is the
second largest angle in the set, so the LEAN carries the mirror on
that world with room to spare. What makes its pair hard to read is
the surface: `MARKINGS["uranus"]` is empty, the globe is bare cyan
and the only feature on the piece is the white ring. That is a
separate question from this one, and this rule does not answer it.
The distinction matters: the rule is about whether the lean can show
the mirror, not about how legible any particular pair turns out to
be.

## What each mirrored world's mirror is carried by

| world | what carries the mirror | what a longitude reflection does not touch |
|---|---|---|
| mercury | seven plains that change hands around a Caloris basin that stays square to the lens | the basin's own longitude, which is within 0.01 degrees of the reflection meridian |
| venus | Aphrodite Terra and the lowlands crossing the ball | nothing: every Venusian marking is an outline with a longitude |
| jupiter | the Great Red Spot, its collar, and the wave phase of the two widest belts | six belts and five zones, which are circles of latitude and have the same longitude everywhere |

Jupiter's row is why its correction needed a `MERIDIAN_ADJUSTMENT`
and the other two worlds' rows do not read the same way. On Mercury
and Venus a reflection moves most of the map. On Jupiter it moves
almost none of it, because almost none of it carries a longitude at
all, and the whole read falls on one 3 mm oval.
`measure/mirror-meridian.md` is the sweep that gave that oval
something to do; the meridian it settles on is -33.7675, which is the
plain mean moved +15.00 degrees.

## Verdict

`markings.MAP_MIRRORED_WORLDS` is ('mercury', 'venus', 'jupiter'), and that is exactly the set
the rule selects from the tilts in `params.PLANETS`: three worlds
under the 20.00 degree floor and five over it, with no world
within 13 degrees of the floor on either side.

Measured by `measure/mirror_set_consistency.py` from
`params.PLANETS` and `parts.markings.MAP_MIRRORED_WORLDS`.
