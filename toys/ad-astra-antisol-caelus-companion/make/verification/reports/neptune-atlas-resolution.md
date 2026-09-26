# Neptune's three cloud bands at globe scale

Neptune's globe is Ø21.89 mm, so its radius is 10.945 mm.

A great circle of a sphere of diameter d is pi*d long and 360
degrees round, so ONE DEGREE OF GREAT-CIRCLE ARC IS pi*d/360.
Here that is pi * 21.89 / 360 = **0.1910 mm**. It is not pi*d/180,
which would give 0.3821 mm and is twice the truth; that doubling is
already in this set's sealed archive and the last section of this
report is about it. Every figure below comes from the 0.1910.

The nozzle is 0.40 mm, the narrowest colour boundary the printer
can lay down, and **2.09 degrees of arc** on this globe.

## The three bands

Each band is a plain `band` region: `features/patches.latitude_band_tool`
draws a torus that meets the globe's own sphere exactly at the two
edge latitudes, so a band declared n degrees wide is n degrees of
arc wide on the printed surface, at every longitude. No taper, no
bow, no tilt and no end: a closed circle of latitude has none.

| band | latitudes | width deg | width mm | nozzle widths | |
|---|---|---:|---:|---:|---|
| `b1` | -46 to -41 | 5 | **0.955** | 2.39 | clears |
| `b2` | +11 to +15 | 4 | **0.764** | 1.91 | clears |
| `b3` | +30 to +33 | 3 | **0.573** | 1.43 | clears |

The narrowest is `b3` at 3 degrees, **0.573 mm**, 1.43 nozzle
widths. It clears the 0.40 mm nozzle, so **no band was widened**;
the three are exactly the three the build carried before the cloud
correction, at the latitudes it recorded for them.

## The gaps between them

Bare globe has to print too: a strip of globe narrower than the
nozzle is a colour boundary the slicer cannot resolve. A band is a
full circle of latitude, so the distance from anything to it runs
along that thing's own meridian and IS the difference in latitude --
longitude can neither shorten nor lengthen it.

| from | to | gap deg | gap mm | nozzle widths | |
|---|---|---:|---:|---:|---|
| `b1` | `b2` | 52 | **9.933** | 24.8 | clears |
| `b2` | `b3` | 15 | **2.865** | 7.2 | clears |
| `b1` | `spot` | 12.00 | **2.292** | 5.7 | clears |
| `b2` | `spot` | 26.00 | **4.967** | 12.4 | clears |
| `b3` | `spot` | 45.00 | **8.596** | 21.5 | clears |

**The widest bare gap between two of the bands is 52 degrees, 9.933 mm**
-- the whole of the southern mid-latitudes and the tropics between
`b1` and `b2`, which is 29 per cent of the globe's own
pole-to-pole span. The tightest gap anywhere on this globe is
12.00 degrees, **2.292 mm**, between `b1` and `spot`: 5.7 nozzle widths
of bare blue.

## The dark spot, which did not move

The owner's instruction is that the dark spot stays exactly as the
build this revision corrects has it. Nothing here was edited, and
this table is the check rather than the claim: the ring is walked
again from `parts/neptune_atlas.SPOT_RING` and measured.

| ring | centre | size | vertices | perimeter mm | shortest edge mm | narrowest neck mm | |
|---|---|---|---:|---:|---:|---:|---|
| `spot` | lat -22, lon -65.2 | 28 x 14 deg of arc = 5.35 x 2.67 mm | 40 | 12.86 | 0.211 | **2.48** | clears |

Its narrowest neck is its own minor axis, 2.48 mm, 6.2 nozzle
widths. Its shortest edge is 0.211 mm, under the nozzle and under
the 0.50 mm least ring edge this set holds its coastlines to; that
is one facet of a smooth curve rather than the width of anything,
and the 40 vertices it comes from are what an independent reader of
a 22-vertex version of this oval asked for. The measurement that
matters for printing is the neck, and it is in the table.

The spot's SOLID contribution is the check that it did not move, and
it is taken on the built colour bodies rather than here.
`measure/neptune-mirror.md` measures the `spot` body on both armies
and compares it against the volume the archived build measured; that
is the number requirement 2 of this revision turns on.

## The companion, which is gone

The build this revision corrects drew a small bright cloud beside
the spot's upper rim. It was `white`, and the marking key in this
set is the filament, so it was one of the nine bodies of the white
cloud marking. Reverting that marking to the three bands takes it
with it, and the drawing being reverted to did not have one.

`ref/neptune-sol.png` does show a bright companion cloud beside the
dark spot and this revision does not draw one. That is a deliberate
loss, recorded in the product's limitations in those terms rather
than left to be found.

## The three figures this report corrects

The sealed archive's copy of this report said, in the paragraph
beginning "Every streak is between 1.35 and 1.65 mm wide", that
this set's other band systems are "3.63 to 7.26 mm (Saturn) and
2.35 to 6.12 mm (Jupiter)", and concluded that Neptune's streaks
were "the narrowest marking family anywhere in the set".

Both figures are wrong and the conclusion drawn from them is wrong.
They came out of the same pi*d/180 doubling the head of this report
derives against, and the run that wrote them had caught that exact
error in its own width figure two paragraphs earlier and repeated
the owner's companion figures without recomputing them.

Read back out of this set's own reports at run time, not typed:

| claim in the sealed report | this set's own measurement | |
|---|---|---|
| Saturn's bands are 3.63 to 7.26 mm | `measure/saturn-atlas-resolution.md` measures the narrowest, the Equatorial Band (`eqb`), at **1.82 mm** | 3.63 is exactly twice 1.82 |
| Jupiter's belts are 2.35 to 6.12 mm | `measure/jupiter-atlas-resolution.md` measures the narrowest belt, the North North Temperate Belt, at **1.18 mm**, and the narrowest zone, the South Tropical Zone, at **1.06 mm** | 2.35 is exactly twice 1.18 |
| Neptune's markings are the narrowest marking family in the set | the streaks that claim described were 1.35 to 1.65 mm, WIDER than Jupiter's 1.18 mm belt and 1.06 mm zone | **the claim was false of the streaks even at the correct numbers** |

### Where the comparison falls now, from the measurement

Neptune's three bands measure 0.955, 0.764, 0.573 mm.
The narrowest band system anywhere else in this set is Jupiter's
South Tropical Zone at 1.06 mm; Saturn's narrowest band is 1.82 mm and Jupiter's
narrowest belt 1.18 mm.

**So Neptune's bands ARE now the narrowest band family in the
set, by a factor of 1.85 against the next narrowest.** That is
the opposite of how the comparison fell for the streaks the
sealed report was describing, and it is stated from the
measurement rather than from the revision brief. In degrees it
is not even close: Neptune's bands are 3 to 5 degrees of arc,
and Jupiter's narrowest zone is 4.5 on a globe 23 per cent
larger, so Neptune loses twice over -- narrower in angle and
smaller in radius.

One thing this does NOT make Neptune, and the distinction is worth
keeping because the sealed claim lost it: narrowest BAND family is
not narrowest marking of any kind. `measure/earth-atlas-resolution.md`
records a strip of green along Australia's outback boundary at
0.40 mm, exactly one nozzle, which is the narrowest deliberate
colour width anywhere in this set. Neptune's 0.573 mm band is the
narrowest thing that runs the whole way round a globe.

## The verdict

| quantity | narrowest mm | nozzle mm | |
|---|---:|---:|---|
| band width | 0.573 | 0.40 | clears |
| bare globe between two markings | 2.292 | 0.40 | clears |
| dark spot at its narrowest neck | 2.48 | 0.40 | clears |

## What is not drawn

Neptune's globe is Ø21.89 mm, so one degree of arc is 0.1910 mm and a 0.4 mm nozzle is 2.09 degrees of it. The spot's bright companion cloud IS drawn, as its own white oval. Considered and refused: a SECOND DARK SPOT -- the reference shows one; POLAR BRIGHTENING -- the reference shows none, and a bright cap on this globe would repeat Saturn's northern cap on the world two ranks below it; RING ARCS -- Neptune has rings, the reference does not show them, this set does not draw them, and a ring on rank 5 would collide with Saturn's role at rank 7 in the size ladder, where the ring IS the rank; a FAINT DARKER CENTRE inside the dark spot, which the reference shows and which would need a fourth filament on a globe held to three; and the reference's own fine cloud texture, whose wisps scale to 0.13 - 0.26 mm here, under one nozzle width, and would print as noise. The set's material rules forbid deliberate grit.
