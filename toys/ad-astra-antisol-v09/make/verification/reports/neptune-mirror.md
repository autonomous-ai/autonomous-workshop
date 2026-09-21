# The two Neptune pieces against each other

Measured on the exact colour bodies `parts/world.py` builds, at
0.0001 mm3. The two armies share one marking description and lean the
opposite way under it; this is what that produces.

## Body for body

| role | filament | solids Sol / Anti | volume Sol mm3 | volume Anti mm3 | difference mm3 | |
|---|---|---:|---:|---:|---:|---|
| `disc` | `white` | 1 / 1 | 4389.3147 | 4393.3048 | +3.9901 | the draft, by design |
| `numeral` | `black` | 2 / 2 | 7.8059 | 7.8059 | -0.0000 | identical |
| `globe` | `blue` | 1 / 1 | 5328.6720 | 5315.6920 | -12.9801 | clipped differently by the disc |
| `spot` | `dark_gray` | 1 / 1 | 11.9319 | 11.9319 | +0.0000 | identical |
| `streaks` | `white` | 9 / 9 | 101.7299 | 114.7099 | +12.9801 | clipped differently by the disc |

## The nine white bodies, one by one

The `streaks` marking is eight cloud streaks and the dark spot's
bright companion, so it comes out as nine separate solids on each
piece. Sorted by volume, because the split order is not the table
order, and paired off: a pair that matches to 0.0001 mm3 is the same
body on both armies.

The `streaks` marking is eight cloud streaks and the dark spot's
bright companion, so it comes out as nine separate solids on each
piece. The split order is not the table order, so the two lists are
paired by MATCHING rather than by position: every Sol body is paired
with the Anti-Sol body nearest it in volume, and a pair inside
0.0001 mm3 is the same body on both armies.

| | volume Sol mm3 | volume Anti mm3 | |
|---:|---:|---:|---|
| 1 | 0.6903 | -- | **Sol only at this volume** |
| 2 | 3.8595 | 3.8595 | identical |
| 3 | 9.8755 | 9.8755 | identical |
| 4 | 13.1112 | 13.1112 | identical |
| 5 | 13.2234 | 13.2234 | identical |
| 6 | 14.0186 | 14.0186 | identical |
| 7 | 15.3674 | 15.3674 | identical |
| 8 | 15.4524 | -- | **Sol only at this volume** |
| 9 | 16.1316 | 16.1316 | identical |
| 10 | -- | 13.1093 | **Anti-Sol only at this volume** |
| 11 | -- | 16.0134 | **Anti-Sol only at this volume** |

**7 of the 9 white bodies come out at exactly the same volume on
both pieces.** The 2 that do not are the two deepest southern
streaks, `s1` at latitude -52 and `s2` at -37. `parts/world.py` cuts
the globe level with the disc's top face, and that plane sits in a
different place in the planet's own frame on the two armies because
the globe leans the opposite way, so a marking far enough south runs
into the disc on one piece and clears it on the other. On Neptune the
disc takes 12.98 mm3 more white off the Sol piece than off the
Anti-Sol one. Those are the same two streaks
`measure/neptune-facing.md` records as Anti-Sol-only features, so the
piece that shows them is the piece that carries all of them.

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
number of solids in every role. 7 of the nine white bodies and the
dark spot are identical in volume to 0.0001 mm3. The 2 that differ, and
the disc, differ for reasons that are in the design rather than in the
build: the mirrored lean against a disc cut that is not mirrored with
it, and the opposite draft that tells the armies apart.
