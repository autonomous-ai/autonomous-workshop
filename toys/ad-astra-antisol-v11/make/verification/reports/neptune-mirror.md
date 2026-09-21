# The two Neptune pieces against each other

Measured on the exact colour bodies `parts/world.py` builds, at
0.0001 mm3. The two armies share one marking description and lean the
opposite way under it; this is what that produces.

## Body for body

| role | filament | solids Sol / Anti | volume Sol mm3 | volume Anti mm3 | difference mm3 | |
|---|---|---:|---:|---:|---:|---|
| `disc` | `white` | 1 / 1 | 4389.3147 | 4393.3048 | +3.9901 | the draft, by design |
| `numeral` | `black` | 2 / 2 | 7.8059 | 7.8059 | -0.0000 | identical |
| `globe` | `blue` | 1 / 1 | 5419.5975 | 5419.5976 | +0.0001 | identical |
| `spot` | `dark_gray` | 1 / 1 | 11.9319 | 11.9319 | +0.0000 | identical |
| `bands` | `white` | 3 / 3 | 10.8043 | 10.8043 | +0.0000 | identical |

## The white bodies, one by one

Neptune's white marking is `bands`, and it comes out as 3 separate
solids on each piece: one per latitude band. The split order is not
the table order, so the two lists are paired by MATCHING rather than
by position: every Sol body is paired with the Anti-Sol body nearest
it in volume, and a pair inside 0.0001 mm3 is the same body on both
armies.

| | volume Sol mm3 | volume Anti mm3 | |
|---:|---:|---:|---|
| 1 | 1.6341 | 1.6341 | identical |
| 2 | 4.4625 | 4.4625 | identical |
| 3 | 4.7077 | 4.7077 | identical |

**3 of the 3 white bodies come out at exactly the same volume on
both pieces**, and the white marking as a whole differs by
+0.0000 mm3 between the two armies.

That is a change from the build this revision corrects, and it is
the direct consequence of what the correction reversed. `parts/world.py`
cuts the globe level with the disc's top face, and that plane sits in
a different half-space of the PLANET's frame on the two armies,
because the globe leans the opposite way. A marking that reaches far
enough south is therefore clipped by the disc on one piece and clears
it on the other -- which is what happened to the two deepest of the
eight cloud streaks the archived build drew, `s1` at latitude -52 and
`s2` at -37, and cost that build 12.98 mm3 of white on one army.

A closed latitude band cannot do that. It is a surface of revolution
about the globe's own polar axis, so mirroring the piece in X maps
each band onto ITSELF rather than onto some other longitude of it,
and the disc's cut takes the same arc out of it on both armies. The
three bands are therefore expected to pair exactly, and they do.

## The dark spot against the build this revision corrects

Requirement 2 of this revision is that the dark spot does not move.
The archived build measured its `spot` body at **11.9319 mm3** on both
armies (`make/verification/reports/neptune-mirror.md` in
`revision-source.zip`). This run measures it at:

| army | archived mm3 | this run mm3 | difference mm3 | |
|---|---:|---:|---:|---|
| Sol | 11.9319 | 11.9319 | -0.0000 | unmoved |
| Anti-Sol | 11.9319 | 11.9319 | -0.0000 | unmoved |

The spot is the same solid it was: same oval, same 40 vertices,
same latitude -22, same longitude, same `dark_gray` filament,
same volume to a ten-thousandth of a cubic millimetre. Nothing
in `parts/neptune_atlas.py`'s spot block was edited, and this is
the check rather than the claim.

## The printed solid

| | Sol | Anti-Sol |
|---|---:|---:|
| disc bed diameter mm | 33.00 | 34.00 |
| disc top diameter mm | 34.00 | 33.00 |
| globe diameter mm | 21.89 | 21.89 |
| north pole leans toward | +X | -X |
| obliquity deg | +28.32 | -28.32 |

`measure/revision-part-hashes.md` shows both printed STEPs coming out
byte-identical to the published set's, which is the other half of the
same statement: this correction moved a colour boundary and nothing
else.

## Verdict

The two pieces carry the same roles, the same filaments and the same
number of solids in every role. 3 of the 3 white bodies and the
dark spot are identical in volume to 0.0001 mm3.
**The disc is the only difference between them**, and it is the
ownership cue: a Sol disc flares as it rises and an Anti-Sol disc
tapers, which costs exactly 3.99 mm3.
