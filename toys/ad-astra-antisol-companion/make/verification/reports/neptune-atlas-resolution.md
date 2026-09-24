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
| `b1` | `companion` | 8.50 | **1.624** | 4.1 | clears |
| `b2` | `companion` | 38.50 | **7.355** | 18.4 | clears |
| `b3` | `companion` | 57.50 | **10.984** | 27.5 | clears |
| `spot` (as cut) | `companion` | 2.20 | **0.420** | 1.1 | clears |

The last row is the pair this revision created, and it is the one
its geometry was solved for. The two ovals OVERLAP as drawn -- the
owner's 8 degrees puts the companion's top inside the spot -- so the
gap in that row does not exist by accident: the spot is cut back
to a keep-out one nozzle width outside the companion. The row is
measured against where the DARK ACTUALLY STOPS -- the spot's own
ring where it runs outside the keep-out, plus the keep-out's ring
where it runs inside the spot -- and not against the spot's undrawn
original outline, which still crosses the companion and would give
a meaningless zero. Two sections below is what it cost.

**The widest bare gap between two of the bands is 52 degrees, 9.933 mm**
-- the whole of the southern mid-latitudes and the tropics between
`b1` and `b2`, which is 29 per cent of the globe's own
pole-to-pole span. The tightest gap anywhere on this globe is
2.20 degrees, **0.420 mm**, between `spot` and `companion`: 1.1 nozzle widths
of bare blue.

## The dark spot, which did not move

The owner's instruction is that the dark spot stays exactly as the
build this revision corrects has it. Nothing here was edited, and
this table is the check rather than the claim: the ring is walked
again from `parts/neptune_atlas.SPOT_RING` and measured.

| ring | centre | size | vertices | perimeter mm | shortest edge mm | narrowest neck mm | |
|---|---|---|---:|---:|---:|---:|---|
| `spot` | lat -22, lon -65.2 | 28 x 14 deg of arc = 5.35 x 2.67 mm | 40 | 12.86 | 0.211 | **2.48** | clears |

Its narrowest neck walks out at 2.48 mm, 6.2 nozzle
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

## The companion, which is back

The owner asked for the dark spot's bright companion cloud on both
Neptune pieces: ONE WHITE OUTLINE OVAL, about 10 by 5 degrees of
arc, at the spot's own longitude, centred about 8 degrees of
latitude south of the spot's centre, and inside the narrowest
feature limit this set already uses for printable markings.

**All five are drawn exactly as asked.** One of them is not free,
and this section is where what it costs is measured rather than
argued: an oval 5 degrees tall centred 8 degrees south of the
centre of an oval 14 degrees tall overlaps it, and the dark spot
is what pays.

| ring | centre | size | vertices | perimeter mm | shortest edge mm | narrowest neck mm | |
|---|---|---|---:|---:|---:|---:|---|
| `companion` | lat -30.0, lon -65.2 | 10 x 5 deg of arc = 1.91 x 0.96 mm | 24 | 4.59 | 0.127 | **0.886** | clears |

**The narrowest the white material gets is 0.886 mm, 2.21 nozzle
widths**, and that is the figure the owner's limit clause asks
for. It is a WALK rather than the declared minor axis, and it comes
out a little under it: the oval is declared 5 degrees of arc
tall, 0.955 mm, and the walk returns 0.886 mm. Two things take the
difference: the ring is a polygon inscribed in the ellipse, so it
is everywhere a little inside it, and the pairs the walk is allowed
to measure sit slightly off the minor axis, where the oval is
already narrowing. Taking the smaller of the two is the
conservative reading and it is the one in the verdict table.
`spot` above is measured the same way and reads under its own
2.67 mm minor axis for the same two reasons. The narrowest
deliberate colour width anywhere
in this set is the 0.40 mm strip of green along Australia's
outback boundary in `measure/earth-atlas-resolution.md`, exactly
one nozzle, so the companion sits 2.21 times clear of the set's
own floor and is not the narrowest marking in the box.

Its shortest ring edge is 0.127 mm. That is a facet of a smooth
curve rather than the width of anything, the same distinction the
dark spot's own 0.211 mm shortest edge is recorded under above, and
the 24 vertices it comes from were set by the ELLIPSE ERROR rather
than copied from the spot's 40: a ring walked at even bearings
falls furthest inside the true ellipse at its two pointed ends,
and that error grows with the size of the oval and falls as the
square of the vertex count.

| ring | semi-axes deg | vertices | end chord falls inside by mm |
|---|---|---:|---:|
| `spot` | 14.0 x 7.0 | 40 | 0.0308 |
| `companion` | 5.0 x 2.5 | 24 | 0.0281 |

The two are the same smoothness to a ten-thousandth of a
millimetre, which is what choosing the count by the error rather
than by the spot's number was for.

### Where it sits: exactly where it was asked for

The companion's centre is **8.0 degrees of latitude south of the
spot's centre**, at the spot's own longitude. Both are the owner's
numbers and both are kept. What they cost is below.

The spot is 14 degrees of arc tall, so its own southern rim is
already 7 degrees south of its centre, and an oval 5 degrees
tall centred at 8.0 puts its top 1.5 degrees INSIDE the spot.

### The move south that was built and rejected

The obvious answer is to move the companion south until a printable
strip of bare globe fits between the two outlines. That needs
11.59 degrees -- the two half-heights plus one nozzle width -- and
it was built at 11.8, rendered, and rejected on the pictures.

`parts/world.py` seats every globe on a cone that springs at
piece-frame latitude -42, and Neptune leans 28.32 degrees, so at
the spot's own longitude the SOL piece's seat collar covers
everything south of about -31 degrees of PLANET latitude. At 11.8
degrees south the oval's centre landed at piece latitude -40.9 and
ten of its twenty-four ring vertices went under the collar: the Sol
army came back with a pale half-lens sitting on its base instead of
an oval. The window between the spot's southern rim and that collar
is about 2.4 degrees of arc, **0.46 mm**, and a marking plus two
nozzle-width gaps does not fit in 0.46 mm at any size.

That is a claim about every size, so it is scanned rather than
asserted. For each half-height, every tenth of a degree of centre
latitude from -36 to -28 is walked and the best either constraint
can be pushed to is reported:

| companion half-height deg | best centre lat | gap to spot mm | nozzle widths | lowest ring vertex on Sol, piece frame | seat at |
|---:|---:|---:|---:|---:|---:|
| 0.8 | -31.43 | 0.3114 | 0.78 | -41.60 | -42.0 |
| 1.0 | -31.48 | 0.2827 | 0.71 | -41.65 | -42.0 |
| 1.2 | -31.52 | 0.2522 | 0.63 | -41.68 | -42.0 |
| 1.4 | -31.45 | 0.2006 | 0.50 | -41.74 | -42.0 |
| 1.6 | -31.35 | 0.1433 | 0.36 | -41.82 | -42.0 |
| 1.8 | -31.27 | 0.0898 | 0.22 | -41.89 | -42.0 |
| 2.0 | -31.21 | 0.0401 | 0.10 | -41.94 | -42.0 |
| 2.2 | -28.60 | 0.0172 | 0.04 | -39.79 | -42.0 |
| 2.4 | -28.60 | 0.0172 | 0.04 | -39.86 | -42.0 |

**No row clears both.** Even at a half-height of 0.8 degrees -- an
oval 0.31 mm tall, already under the nozzle and unprintable as a
marking -- the best gap reachable is 0.31 mm. There is no oval at
this longitude that stands clear of the spot AND clear of the
collar, so the choice is not between a good placement and a bad
one; it is between overlapping the spot and losing a third of the
oval into the base on one army.

### How the companion and the spot are kept apart

The owner's 8 degrees puts the companion's top 1.5 degrees inside
the spot, and this set's rule for two markings is that they either
share a boundary exactly -- the way Earth's ice shares one with its
land -- or they stand at least one nozzle width of bare globe
apart. Two ovals that CROSS do neither: their outlines meet at a
point and open from zero, leaving a wedge of bare blue thinner than
the nozzle at each end of the companion.

**Sharing a boundary was built first and rejected by an independent
reader.** With the spot subtracted back to the companion itself the
two colours touch, and a critic shown the finished renders cold
called the pair "a notched figure-eight" and the new marking "a
small grey circle" -- a lobe budding off the dark spot rather than
a cloud beside it. The figure the owner asked for was inverted.

So the spot is cut to a KEEP-OUT instead: the companion's own oval
grown by 2.30 degrees of arc, a shape that is never drawn and never
printed. What survives between the two markings is bare globe.

| quantity | value |
|---|---:|
| the companion's rim, all of it | 4.589 mm |
| ... running inside the spot's ORIGINAL outline | 1.696 mm |
| ... closer to the spot's original outline than one nozzle | 0.922 mm |
| companion outline to KEEP-OUT outline, at their closest | **0.4208 mm** |
| companion outline to where the DARK STOPS, at their closest | **0.4203 mm** |

**37 per cent of the companion's rim would have been a shared
colour boundary, and 0.922 mm of the rest would have run closer to
the dark than the printer can resolve. Neither survives.** The
keep-out holds the dark back to **0.4208 mm** at the closest point
anywhere, which is 1.05 nozzle widths, and the dilation that buys
it was SOLVED rather than guessed: the offset of an ellipse is not
an ellipse, so growing both half-axes by one nozzle width leaves
the two curves closer than a nozzle somewhere in between. 2.30 is
the smallest hundredth of a degree at which the measured minimum
reaches the nozzle, and the row above re-measures it on the rings
the build actually walked.

### What it costs the spot, measured

A bay, and it is larger than the companion because the keep-out is
larger than the companion. The keep-out is 14.6 by 9.6 degrees of
arc against the companion's 10 by 5, and where it crosses the
spot it takes a bay about 15 degrees of arc wide out of the spot's
southern rim, reaching about 3.7 degrees up into a 28 by 14 oval.
**That is a real change to the Great Dark Spot and it is the price
of the owner's own 8 degrees.** It is disclosed in the product's
limitations, in `antisol_spec.md` item 26 and in
`measure/neptune-mirror.md`, which measures the spot's own region
BEFORE the cut against the volume the archive sealed and accounts
every cubic millimetre of the difference to the keep-out.

The spot's ring is not edited: its latitude, longitude, half-axes,
40 vertices and `dark_gray` filament are byte-identical in the
source, and `measure/neptune-facing.md` reproduces its archived dot
products at every frame. What changed is where the dark stops.

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
| bare globe between two markings | 0.420 | 0.40 | clears |
| dark spot at its narrowest neck | 2.48 | 0.40 | clears |
| companion at its narrowest neck | 0.886 | 0.40 | clears |

Every colour boundary on this globe clears the nozzle, including
the one this revision created: the narrowest strip of bare blue
anywhere between two markings is the 0.4203 mm the keep-out holds
between the companion and the dark spot.

## What is not drawn

Neptune's globe is Ø21.89 mm, so one degree of arc is 0.1910 mm and a 0.4 mm nozzle is 2.09 degrees of it. DRAWN, and new in this revision: the dark spot's BRIGHT COMPANION CLOUD, one white oval 10 by 5 degrees of arc at the spot's own longitude, 8.0 degrees of latitude south of the spot's centre, which overlaps the spot's southern rim by 1.5 degrees and takes a scallop out of it by subtraction rather than moving south, because south of about 9 degrees the Sol piece's seat collar covers the oval. Considered and refused: a SECOND DARK SPOT -- the reference shows one; POLAR BRIGHTENING -- the reference shows none, and a bright cap on this globe would repeat Saturn's northern cap on the world two ranks below it; RING ARCS -- Neptune has rings, the reference does not show them, this set does not draw them, and a ring on rank 5 would collide with Saturn's role at rank 7 in the size ladder, where the ring IS the rank; a FAINT DARKER CENTRE inside the dark spot, which the reference shows and which would need a fourth filament on a globe held to three; and the reference's own fine cloud texture, whose wisps scale to 0.13 - 0.26 mm here, under one nozzle width, and would print as noise. The set's material rules forbid deliberate grit.
