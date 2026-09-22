# How far apart the two pieces of each pair read

## One: the lean

`features.planet_frame` turns the Sol globe about +Y by the planet's
true obliquity and the Anti-Sol globe by minus it, so the two poles
stand apart by twice the tilt -- or by 360 less twice the tilt when
that exceeds a half turn, because a lean of +177.36 and one of
-177.36 are the same turn measured each way round. This is pure
arithmetic on `params.PLANETS`; nothing here is built.

| world | obliquity | the two poles stand apart by | the lean gives the pair |
|---|---:|---:|---|
| mercury | 0.03 | 0.06 degrees | **nothing** |
| mars | 25.19 | 50.38 degrees | a plain difference |
| venus | 177.36 | 5.28 degrees | **nothing** |
| earth | 23.44 | 46.88 degrees | a plain difference |
| neptune | 28.32 | 56.64 degrees | a plain difference |
| uranus | 97.77 | 164.46 degrees | a plain difference |
| saturn | 26.73 | 53.46 degrees | a plain difference |
| jupiter | 3.13 | 6.26 degrees | **nothing** |

Three worlds are degenerate and five are not. Mercury at 0.06
degrees and Venus at 5.28 are the two this correction is for.
Jupiter at 6.26 has the same condition and is NOT in scope: the
owner named Mercury and Venus and did not name it. Mars at 50.38,
Earth at 46.88, Saturn at 53.46, Neptune at 56.64 and Uranus at
164.46 are nowhere near it, which is the negative half of the same
check and is why the recommendation below is scoped to Jupiter alone.

## Two: the surface

Measured on the built colour bodies. Every marking solid's centre of
mass gives a direction out of the globe's centre; that direction is
projected into the camera's image plane at the two photographed
frames. Distances are millimetres on that globe's own surface.

- **separation** -- how far a marking is from the nearest marking of
  the same filament on the other piece. Near zero means the pair is
  one object photographed twice.
- **mirror residual** -- the same distance measured against a
  left-to-right flip of the other piece's picture. Near zero means
  the pair reads as a mirror pair rather than as two unrelated faces.

Both are volume-weighted, so a large province counts for more than a
sliver, and both are symmetrised over the two directions.

| world | globe Ømm | frame | visible markings, Sol / Anti | separation | mirror residual |
|---|---:|---|---|---:|---:|
| mercury | 13.78 | hero | 5 / 4 | 2.512 | 1.215 |
| mercury | 13.78 | state sheet | 5 / 5 | 2.720 | 0.753 |
| mars | 14.72 | hero | 5 / 6 | 4.217 | 4.668 |
| mars | 14.72 | state sheet | 5 / 5 | 3.875 | 3.885 |
| venus | 16.53 | hero | 3 / 3 | 4.722 | 0.386 |
| venus | 16.53 | state sheet | 3 / 3 | 4.669 | 2.531 |
| earth | 16.70 | hero | 6 / 6 | 3.771 | 4.928 |
| earth | 16.70 | state sheet | 7 / 6 | 3.596 | 4.367 |
| neptune | 21.89 | hero | 3 / 4 | 6.936 | 5.855 |
| neptune | 21.89 | state sheet | 3 / 4 | 6.064 | 7.820 |
| uranus | 22.02 | hero | 0 / 0 | no marking | no marking |
| uranus | 22.02 | state sheet | 0 / 0 | no marking | no marking |
| saturn | 26.00 | hero | 4 / 5 | 10.734 | 4.143 |
| saturn | 26.00 | state sheet | 4 / 4 | 9.548 | 4.774 |
| jupiter | 26.97 | hero | 7 / 7 | 1.238 | 0.368 |
| jupiter | 26.97 | state sheet | 7 / 8 | 4.214 | 3.864 |

Uranus has no marking of any kind since the run before this one --
one undivided cyan sphere -- so there is nothing on its surface to
compare and the row says so rather than reporting a zero. Its pair is
separated by the lean, at 164.46 degrees, and by the plane its ring
stands in, which follows that lean.

## Read in rank order, on the frame that separates them least

| world | obliquity | lean | least surface separation | reads as |
|---|---:|---:|---:|---|
| mercury | 0.03 | 0.06 | 2.512 mm (36% of the globe radius) | two different objects |
| mars | 25.19 | 50.38 | 3.875 mm (53% of the globe radius) | two different objects |
| venus | 177.36 | 5.28 | 4.669 mm (56% of the globe radius) | two different objects |
| earth | 23.44 | 46.88 | 3.596 mm (43% of the globe radius) | two different objects |
| neptune | 28.32 | 56.64 | 6.064 mm (55% of the globe radius) | two different objects |
| uranus | 97.77 | 164.46 | no marking | the lean alone, at 164.46 degrees |
| saturn | 26.73 | 53.46 | 9.548 mm (73% of the globe radius) | two different objects |
| jupiter | 3.13 | 6.26 | 1.238 mm (9% of the globe radius) | **one object photographed twice** |

The share of the globe radius is the honest way to compare across the
ladder: Mercury's globe is Ø13.78 and Jupiter's Ø26.97, so a
millimetre means about twice as much on the smaller ball.

## Measured by

`measure/pair_separation.py`, on the solids `parts/world.py` builds
and the cameras in `snap_frames.py`.
