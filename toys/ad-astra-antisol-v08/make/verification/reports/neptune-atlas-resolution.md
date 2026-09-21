# Neptune's cloud streaks at globe scale

Neptune's globe is Ø21.89 mm, so its radius is 10.945 mm and one
degree of great-circle arc is 0.1910 mm.  The nozzle is 0.40 mm,
which is the narrowest colour boundary the printer can lay down
and 2.09 degrees of arc here.

The owner's width decision is 1.5 mm.  On this globe that is
7.85 degrees of arc, not the 3.93 the brief also states -- 3.93
degrees is 0.75 mm here.  The millimetre is what is drawn and what
is measured below; `parts/neptune_atlas.py` records the correction.

## Every streak

A streak TAPERS: it is at its drawn width across the middle and
40 per cent of it at each end, so two widths are measured. `middle`
is the distance between its two long sides at the centre and `end`
is the ring's own narrowest neck, which on this shape is the width
across the rounded end -- the narrowest colour boundary the printer
is asked to lay down anywhere on this streak.
`length` is the centreline's great-circle arc; the brief specifies a
streak's length in degrees of longitude, and a degree of longitude
is cos(latitude) of a degree of arc, so both are given.

| streak | lat | lon | tilt | drawn mm | length deg lon | length deg arc | length mm | aspect | vertices | shortest edge mm | middle mm | end mm | |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `s1` | -52 | -14.5 | +4 | 1.40 | 90 | 55.4 | 10.58 | 7.6:1 | 44 | 0.20 | 1.40 | 0.72 | clears |
| `s2` | -37 | -77.6 | -11 | 1.55 | 76 | 60.7 | 11.59 | 7.5:1 | 48 | 0.27 | 1.55 | 0.87 | clears |
| `s3` | -10 | -102.5 | +7 | 1.35 | 46 | 45.3 | 8.65 | 6.4:1 | 38 | 0.18 | 1.35 | 0.69 | clears |
| `s4` | +4 | -108.4 | -3 | 1.60 | 60 | 59.9 | 11.43 | 7.1:1 | 48 | 0.26 | 1.60 | 0.86 | clears |
| `s5` | +17 | -22.2 | +12 | 1.45 | 54 | 51.6 | 9.86 | 6.8:1 | 42 | 0.28 | 1.45 | 0.88 | clears |
| `s6` | +28 | +18.5 | -6 | 1.50 | 72 | 63.6 | 12.14 | 8.1:1 | 50 | 0.21 | 1.50 | 0.73 | clears |
| `s7` | +38 | -44.2 | +3 | 1.65 | 58 | 45.7 | 8.73 | 5.3:1 | 38 | 0.28 | 1.65 | 0.96 | clears |
| `s8` | +47 | -114.9 | -9 | 1.50 | 84 | 57.3 | 10.94 | 7.3:1 | 46 | 0.23 | 1.50 | 0.79 | clears |

Every streak is between 1.35 and 1.65 mm wide across its middle,
against the family's
nominal 1.50 mm and the nozzle's 0.40 mm.  For scale, this set's
other band systems are 3.63 to 7.26 mm (Saturn) and 2.35 to 6.12 mm
(Jupiter), so Neptune's streaks remain the narrowest marking family
anywhere in the set.

## The dark spot and its companion

The companion is a STREAK rather than an oval, so it is measured the
way the eight streaks above are: by its own narrowest neck. It is
drawn as a wisp because an independent reader of the first build of
this correction read a small oval beside the spot as a stray droplet
that had broken off it, which is the opposite of what it is for.

| ring | size | vertices | perimeter mm | shortest edge mm | narrowest neck mm | |
|---|---|---:|---:|---:|---:|---|
| `spot` | 28.0 x 14.0 deg of arc = 5.35 x 2.67 mm | 40 | 12.86 | 0.21 | 2.48 | clears |
| `companion` | 15 deg of longitude = 2.83 mm long, 1.45 mm wide | 18 | 7.99 | 0.25 | 1.18 | clears |

The companion is 53 per cent of the spot's length and 54 per cent
of its height, so it cannot be read as a second dark spot or as part
of the first.

The gap between the spot and its companion is **0.61 mm**, clear of the
0.40 mm nozzle.  The brief's rule if that gap were short is to move
the companion rather than shrink it, and that is the rule the
companion's latitude is set by: its size was chosen against the
spot's first and the gap decided where it sits.

## The gap between every pair of markings

Two markings running closer than the nozzle print as one.  Every
pair of the ten rings on this globe is measured; the table lists
every pair closer than 3.00 mm, which is where the question stops
being interesting.  Rings are resampled to 0.05 mm before
comparison, because the closest approach rarely falls on a vertex.

| pair | gap mm | |
|---|---:|---|
| `s7` / `s8` | 0.57 | clears |
| `companion` / `spot` | 0.61 | clears |
| `s6` / `s7` | 0.67 | clears |
| `s5` / `s6` | 0.69 | clears |
| `s1` / `s2` | 0.82 | clears |
| `s3` / `companion` | 1.21 | clears |
| `s2` / `spot` | 1.23 | clears |
| `s3` / `s4` | 1.30 | clears |
| `s3` / `spot` | 1.75 | clears |
| `s4` / `companion` | 2.02 | clears |
| `s2` / `s3` | 2.79 | clears |
| `s5` / `s7` | 2.82 | clears |

The closest approach anywhere on this globe is **0.57 mm**.

## The verdict

Three quantities decide whether this globe prints, and all three are
widths of MATERIAL: how wide the colour region is where it is
narrowest, and how wide the bare globe is between two regions.

| quantity | narrowest mm | nozzle mm | |
|---|---:|---:|---|
| streak width across its middle | 1.35 | 0.40 | clears |
| streak width at its narrowest end | 0.69 | 0.40 | clears |
| gap between two markings | 0.57 | 0.40 | clears |

## The shortest ring edge, and why it is not in that table

The shortest edge of any ring on this globe is 0.18 mm, under the
0.40 mm nozzle and under the 0.50 mm least ring edge this set holds
its coastlines to. That is reported here rather than hidden, and it
is not a printability finding, because it is not the width of
anything. Every edge that short is one facet of a streak's rounded
END: the end is a half-disc of radius 0.27 to 0.33 mm cut into four
segments, so its chords are necessarily shorter than the 0.69 to
0.96 mm feature they approximate. The 0.50 mm margin exists for a
coastline ring, where a short edge can pinch the region it bounds to
nothing; here it cannot, and the measurement that proves it is the
`end mm` column above -- the narrowest the material itself gets,
measured on the ring rather than inferred from it. Cutting the ends
into two segments instead of four would put every edge over the
nozzle and would replace a rounded end with a chisel point, which is
the shape the correction exists to avoid.

## What is not drawn

Neptune's globe is Ø21.89 mm, so one degree of arc is 0.1910 mm and a 0.4 mm nozzle is 2.09 degrees of it. Considered and refused: a SECOND DARK SPOT -- the reference shows one and the brief forbids a second; POLAR BRIGHTENING -- the reference shows none, and a bright cap on this globe would repeat Saturn's northern cap on the world two ranks below it; RING ARCS -- Neptune has rings, the reference does not show them, this set does not draw them, and a ring on rank 5 would collide with Saturn's role at rank 7 in the size ladder, where the ring IS the rank; a FAINT DARKER CENTRE inside the dark spot, which the reference shows and which would need a fourth filament on a globe the brief holds to three; and the reference's own fine cloud texture, whose wisps scale to 0.13 - 0.26 mm here, under one nozzle width, and would print as noise. The set's material rules forbid deliberate grit.
