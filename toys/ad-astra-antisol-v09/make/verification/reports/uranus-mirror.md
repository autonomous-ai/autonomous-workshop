# The two Uranus pieces against each other

Measured on the exact colour bodies `parts/world.py` builds, at
0.0001 mm3. The two armies share one marking description, one ring
description and one obliquity, and lean the opposite way under all
three; this is what that produces.

## Body for body

| role | filament Sol / Anti | solids | volume Sol mm3 | volume Anti mm3 | difference | |
|---|---|---:|---:|---:|---:|---|
| `disc` | `white` / `black` | 1 / 1 | 4388.653338 | 4392.643479 | +3.990141 | the draft runs the other way: Ø33.00 to Ø34.00 against Ø34.00 to Ø33.00 |
| `numeral` | `black` / `white` | 2 / 2 | 8.467313 | 8.467231 | -0.000082 | the same digit in the same place, in the other filament |
| `globe` | `cyan` / `cyan` | 1 / 1 | 5323.412261 | 5323.412312 | +0.000051 | clipped by a disc that drafts the other way |
| `hood_north` | `beige` / `beige` | 1 / 1 | 109.588671 | 109.588675 | +0.000003 | identical |
| `hood_south` | `beige` / `beige` | 1 / 1 | 109.588675 | 109.588671 | -0.000003 | identical |
| `ring` | `cyan` / `cyan` | 1 / 1 | 54.830480 | 54.830494 | +0.000014 | identical |

**The two hoods and the ring are identical to 0.0001 mm3 on both armies.**
That is the answer this correction needed: a hood is a flush inlay and
a ring is added material, and neither depends on which way the piece
leans. The three bodies that do differ are the three the set means to
differ, and they differ by the draft rather than by the marking.

## The ring in space

A mirror in X, which is what the two armies are: the Sol ring's
greatest +X reach is the Anti-Sol ring's greatest -X reach, and
everything square to X is unchanged.

| | Sol | Anti-Sol | mirrored value | |
|---|---:|---:|---:|---|
| X low mm | -1.7340 | -2.1191 | -1.7340 | mirrored |
| X high mm | 2.1191 | 1.7340 | 2.1191 | mirrored |
| Y low mm | -12.0100 | -12.0100 | -12.0100 | mirrored |
| Y high mm | 12.0100 | 12.0100 | 12.0100 | mirrored |
| Z low mm | 5.0000 | 5.0000 | 5.0000 | mirrored |
| Z high mm | 25.9773 | 25.9773 | 25.9773 | mirrored |

## The printed solid

| | Sol | Anti-Sol | |
|---|---:|---:|---|
| solids | 1 | 1 | one printed part each |
| volume mm3 | 9994.4555 | 9998.5282 | the disc's draft, +4.0727 mm3 |
| height mm | 25.9773 | 25.9773 | identical |

The printed parts differ in volume by 4.0727 mm3 on a 9994 mm3 piece,
0.04 per cent, and 3.9901 of that is the two discs' own draft. The
remaining 0.0825 mm3 is not a second difference in the design: the
printed part is built from the disc and the ball directly, in three
booleans, and the colour bodies are built by splitting the same solid
fifteen ways, so the two paths round the drafted seam between disc and
globe a few hundredths of a cubic millimetre apart. Both are far under
one layer of one extrusion.

## Verdict

**The two pieces are exact mirrors.** Every body that is meant to
match matches to 0.0001 mm3, the two hoops lean opposite ways and reach
the same distance in the other direction, and the three bodies that
differ differ by the disc's draft alone.

Measured by `measure/uranus_mirror.py` on the built solids.
