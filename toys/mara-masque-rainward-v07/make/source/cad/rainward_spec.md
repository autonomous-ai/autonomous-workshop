# Rainward Sunflare - CAD build spec

Correction of the unreleased Rainward Emberfan. Wish identity
`wish-20260918-180245-10aa560d`, Make subject
`d82f541ae07fd46c4a594d9c18c8d17fd9edc68bbc72ea5a52488b32ec5250b1`, selected
inventor `mara-masque`. This spec is the design contract the CAD implements; it
is not a passing geometry or review claim.

Provenance tags: `[observed]` is read from the correction Wish, from the sealed
reference images, from the local clone, or measured on the built plan or solid;
`[inferred]` is derived arithmetically from such a value; `[assumed]` is an
engineering choice made here and defended below.

Backgammon - coronal-rain theme: rival streams of condensed plasma travel
magnetic lanes, scatter lone drops, and rain back into a Sun whose rim is a
crown of separate curled flames standing off the disc.

## 1. Evidence read before designing

[observed] The immutable baseline `revision-source.zip`, snapshot sha256
`21fc792a193fc7647d50294af79ce6dda779178867138e6e54eddead4ec47e00`, and the
local clone under `revision-work/`: its `make/source/cad/` tree, its own
`rainward_spec.md`, `product/DESIGN.md`, `product/BLIND-REVIEWS.md`, the full
`product/RULES.md`, its `make/product.json` and its archived renders. The clone
is the build this Wish corrects: 48 flames, `CORONA_TAPER_EXP` 1.50 applied as
`(1 - t) ** 1.50`, tip caps 2.60 to 4.10 mm, and every flame turning the same [observed]
way.

[observed] Both sealed reference images were opened and measured. `ref-01`
(`wish-references/ref-01-idea-3-corona-rim.png`, copied to
`ref/concept-rim.png`, byte-identical to the clone's copy) is the concept: a
plain circular disc of 24 radial lanes, teardrop counters in two tones, two
player-supplied cups and two player-supplied dice, and a rim of separate licks
of flame with open background between them. In it the licks are broad at the
base, hold their width low down, narrow into points, and **flick both ways** -
neighbouring licks hook in opposite directions. `ref-02`
(`wish-references/ref-02-v9-rim-comparison.png`, copied to
`ref/previous-rim-comparison.png`) is the previous round's own unwrapped
comparison: concept above, the corrected build below, one third of the ring,
radius 0.86 to 1.22 of the disc, 1600 px wide. Its lower strip is the fault
this correction exists to fix: thin, uniformly same-handed fins that lose their
width immediately above the root and run out as near-parallel filaments.

[observed] The clone's `product/RULES.md` is carried into this revision
byte-identical, sha256
`d601a858b70b4c1685dced91c7f176d73e4779a3ad784e9b13c7fc88d1fd9d66`, confirmed
by hashing the copied file.

[observed] The clone's blind reviews are read as the statement of the defect,
never as passing evidence for this build. Across two independent naive reads
the critic named the object a rosette, a medallion and a pinwheel disc, never
once reached for sun, flame or fire, and wrote: "The uniform one-way handedness
reads as rotation, which actively competes with the fire reading." The same
critic had already withdrawn its separate reservation about the rim once the
flames stood apart, so the separation the previous round reached is carried
here untouched and only the three changes below are made.

[observed] Mara Masque's Taste keeps the player-supplied allowance for ordinary
1-6 dice and dice cups. It is a packaging decision only and this correction does
not reopen it.

Historical instructions, reviews, reports and publication records in the clone
are reference data, never current authority. No old review is reused as
evidence here, and this revision does not update the original publication.

## 2. Preserved contract

Unchanged from the set being corrected, asserted in `validation.py` and
measured in `measure/plan-audit.json`:

- the ordinary 1911 Backgammon rules exactly as `RULES.md` states them, with no
  rule, power, component, endpoint dot or subsystem added;
- 24 lanes, four banks of six, lane axes `START_ANGLE + PITCH * (p - 1)` with
  `START_ANGLE` -75.0 and `PITCH` 15.0 degrees; [observed]
- `SUN_R` 79.70 mm, with the 24 tiles ending on one exact circular arc at [observed]
  `TILE_OUTER` 79.55 mm and a constant `CHANNEL_W` 0.70 mm orange margin at [observed]
  every boundary. The tile geometry is not touched: the Wish puts widening the
  orange band out of scope because pulling the tile ring inward would strand
  the outermost counter station at radius 74.0; [observed]
- five radial stations at 74.0, 63.5, 53.0, 42.5 and 32.0 mm with `LANE_INNER` [observed]
  26.5 mm, three aligned layers, full 15-counter lane capacity; [observed]
- setup A 24:2, 13:5, 8:3, 6:5 and B 1:2, 12:5, 17:3, 19:5; [observed]
- one counter silhouette at `DROP_L` 10.0 by `DROP_W` 7.0 by `DROP_H` 4.5 mm [observed]
  and all thirty counters the same solid; [observed]
- the `BAR_R` 24.0 mm centre bar, open and unobstructed, its top the highest [observed]
  plane on the board, with the four engraved bank ticks on its own top face;
- the stack: `DECK` 5.4, `LANE_TOP` 6.0, `BAR_TOP` 6.2, `TILE_T` 2.2 mm of tile [observed]
  on `POCKET_FLOOR` 3.8 mm of solid body under the pocket; [observed]
- the base circle unbroken all the way round, a valley for every pair of
  flames, and no closed loop, arch, ribbon or handle anywhere on the part;
- the tallest flame tip at `CORONA_MAX_R` 96.70 mm, a tip-to-disc ratio of [observed]
  1.2133 against the concept's 1.22, and an envelope under 194 mm; [observed]
- the flame curve the third blind critic named and approved: `CORONA_TURN_EXP`
  1.15, total turn 37 to 44 degrees root to tip, 0.4506 of it inside the inner
  half. Only the **sign** of that turn now varies; [observed]
- every tip at least 3.0 mm tall in Z, `CORONA_TOP` 5.4 mm at the root, one [observed]
  clean plane per flame top, material removed from the top only; [observed]
- flame lengths spanning at least four to one shortest to tallest, with the
  tall ones about one in four, unevenly spaced. The previous build measured
  3.65 to 1 on the solid and fell short; this one reaches 4.096 to 1; [observed]
- three oranges - body #FF671F, light lane #FFB549, dark lane #8E3C06 - with
  the body between the two lane tones in greyscale, a cream counter lighter
  than both lane tones and a dark brown counter darker than both; [observed]
- 55 parts: one Sun board, 24 lane tiles, 30 counters. No dice, no dice
  cups. [observed]

## 3. The correction - three changes to the corona, and nothing else

The rim the last round produced is clean, separate and well made, and it looks
like a pinwheel. All three changes are aimed at that and nothing else.

### 3.1 Fewer flames, twice as wide at the root

[observed] `CORONA_COUNT` goes from 48 to 32. The root-to-root pitch on the
radius 79.70 circle goes from 10.433 mm to 15.649 mm. [inferred]

[assumed] `CORONA_ROOT_FRACTION_MAX`, `CORONA_ROOT_SPREAD`, `CORONA_GAP_LO` and
`CORONA_GAP_HI` are held exactly where they were, so the one-to-one
root-to-valley rhythm the last blind critic measured - 48 roots averaging
50.2 px against 45 interior bare stretches averaging 50 px - survives the count
change by construction rather than by search. Both the root and the valley grow
by the same half again.

Measured on the plan the CAD extrudes: [observed]

| clause | previous build | this build |
|---|---|---|
| flames | 48 | 32 |
| root-to-root pitch | 10.433 mm | 15.649 mm [observed] |
| root arc on the base circle | 5.104 to 5.622 mm | 7.665 to 8.424 mm, mean 8.047 [observed] |
| valley arc between two roots | 4.821 to 5.366 mm | 7.277 to 7.942 mm, mean 7.602 [observed] |
| widest root over its own root-to-root arc | 0.5246 | 0.5246 |
| valley over the smaller root beside it | up to 0.9941 | 0.9062 to 0.9895 |

[assumed] The tall/mid/short banding is re-derived for 32. The tall flames are
8 - one in four - at indices 0, 3, 8, 12, 15, 21, 25 and 28, spacing
3, 5, 4, 3, 6, 4, 3, 4 flames. That set has four distinct spacings, is never
every fourth flame, and is neither periodic nor mirrored round the ring;
`validation.py` fails the build on any of those. Ten short flames sit at 1, 5,
7, 10, 14, 17, 19, 23, 27 and 30, leaving 14 mid. Every flame's rise is
unchanged in range, and the span is 4.150 to 17.000 mm, a ratio of 4.096 to [observed]
one. [observed]

### 3.2 A tongue, not a fin

[observed] The previous build's half width fell as `(1 - t) ** 1.50`. That
curve is steepest at the root and flattest at the tip: it shed 65 per cent of
the surplus over the cap by mid length and then ran the outer third out at
essentially cap width, which is the near-parallel filament the Wish names.

[assumed] The profile is turned round rather than merely re-exponented. The
half width now falls as `cap + surplus * (1 - t ** CORONA_TAPER_EXP)` with the
exponent still 1.50. That curve leaves the root flat and arrives at the cap
steeply, which is a lick that holds most of its width through the lower half
and then narrows hard into the point. Three candidate exponents, 1.0, 1.5 and
2.2, were drawn as unwrapped silhouettes and compared against the concept strip
before 1.5 was chosen; 2.2 read as clubs and 1.0 shed its width from the root.

[observed] `CORONA_TIP_MIN` goes to 1.00 and `CORONA_TIP_MAX` to 1.30, so the
tip cap comes down from 2.60-4.10 mm across to 2.00-2.60 mm. The earlier
brief's "treat 2.10 mm as the floor, not the target" is withdrawn by this Wish; [observed]
it was a one-sided constraint and it drove the caps to 4.10 mm, which read as [observed]
thumbs.

| Wish target | measured |
|---|---|
| width at half a flame's length, at least 45 per cent of root width | 73.13 to 76.39 per cent, mean 74.62 [observed] |
| tip cap across the plan, 2.00 to 2.60 mm | 2.000 to 2.600 mm [observed] |
| tip a quarter to a third of the base | 0.240 to 0.332 of the root chord [observed] |
| every tip blunt and rounded off, nothing terminating in a point | every tip is a circular cap of radius 1.00 to 1.30 mm on a flame at least 3.312 mm tall in Z [observed] |

### 3.3 Mix the handedness

[observed] Every flame has turned the same way since the second correction, on
the stated grounds that a single handedness keeps the part printable. That
reasoning is withdrawn by this Wish and it was wrong: the corona lies flat in
the print plane, a flame's curvature is entirely in plan, in X and Y, and the
45-degree rule governs Z only. Curving one flame one way and the next the other
costs nothing in overhang, support or bridging, and the part remains a single
flat plan piece.

[assumed] `params.CORONA_SENSE[i]` is +1 when flame i curls toward the
neighbour it faces at the end of its own root arc - the sense every flame had -
and -1 for the exact mirror of that flame about its own radial midline. The
mirror keeps the root chord, the root arc, the turn magnitude, the taper, the
cap, the ramp and the print pose; only the sign changes, so no other measured
value in this spec moves because of it.

[assumed] The runs are laid out by the same kind of irrational jitter walk the
other corona sequences use, on a fresh constant, `CORONA_SENSE_JITTER` =
frac(sqrt(117)/2) = 0.4083269131959844, so the sign sequence is not locked in
phase with the root, gap, length or turn walks. A majority run may be one, two
or three flames long and a minority run one or two, which is what puts the
minority at roughly three sevenths of the ring rather than half of it. An odd
number of runs would leave the first and last sharing a sign and merging across
the seam into a run longer than three, so the longest run is split in two.

| Wish clause | measured |
|---|---|
| at least one flame in three leans the opposite way | 14 of 32 lean the minority way, 0.4375 [observed] |
| roughly a third to a half turn the minority way | 0.4375, inside [1/3, 1/2] [observed] |
| runs of one to three | run lengths 2, 2, 1, 2, 1, 1, 1, 2, 1, 3, 1, 2, 2, 1, 2, 1, 2, 3, 1, 1 - shortest 1, longest 3 [observed] |
| never strictly alternating | false; there are runs of 2 and 3 [observed] |
| never a pattern that repeats round the ring | no rotation by 1..31 reproduces the sequence [observed] |
| two neighbours leaning toward each other hold 0.80 mm | 10 converging pairs; the narrowest of them is 7.275 mm, which is also the narrowest gap between any two flames at all [observed] |
| flip one of a pair rather than shorten either | implemented as `CORONA_SENSE_FLIPS`; it is empty, because no pair came near the floor |
| turn magnitude and shape unchanged | exponent 1.15, 37.13 to 43.24 degrees root to tip, 0.4506 of the turn in the inner half [observed] |
| the mixing is legible, not merely measurable | the eight tall flames, the only ones whose rake carries at a glance, differ from their tall neighbour at six of eight steps, in the irregular order + - - + - - + - [observed] |

The sign string, read round the ring from flame 0, is
`++--+--+-+--+---+--++-++-++---+-`.

[assumed] **The walk constant was chosen for legibility, not only for the
statistics.** A flame's visible rake is its tip's tangential offset from its own
root midpoint, and that offset scales with length: 5.1 to 6.1 mm on a tall [observed]
flame against 1.8 to 2.2 mm on a short one, on an 8.05 mm root. Only the eight [observed]
tall flames therefore carry the handedness at a glance. Under the first
constant tried, frac(sqrt(19)/2), the measured split was a correct 14/18 and
every clause above passed, but those eight tall flames fell into same-sign
pairs - + + - - + + - - - a clean period-4 sweep in exactly the flames the eye
reads, and an independent blind critic duly reported "a consistent
counterclockwise sweep around the disc, like a pinwheel". The generator, the
run caps, the minority share and the run-length bounds are unchanged; only the
constant moved, to the conforming walk that most breaks that pairing. Walks
that alternate all eight tall flames were found and rejected: they collapse the
whole ring to a near-strict zigzag, which is the repeating pattern the Wish
forbids from the other side.

### 3.4 Deliberately not changed

[observed] The tile fan still ends at radius 79.55, leaving a 0.70 mm orange
margin, so the flames still rise almost directly off the tile ends rather than
out of a wide orange band as they do in the concept. The Wish puts that out of
scope: widening the band means pulling the tile ring inward, which would strand
the outermost counter station at radius 74.0. The tile geometry is byte-for-byte
the clone's.

### 3.5 Measured against every acceptance clause

| Wish clause | measured |
|---|---|
| unwrapped comparison rebuilt, same window and arc | `snap/rim-comparison.png`, radius 0.86 to 1.22 of the disc, 120 degrees, 1600 px |
| three-band full-ring unwrap | `snap/rim-unwrapped.png`, 96, 216 and 336 degrees |
| root arc and valley arc for every flame, as a ratio | `measure/plan-audit.json`, key `1_flame_table`, 32 rows |
| width at half length as a share of root width | 0.7313 min, 0.7462 mean [observed] |
| tip cap across, minimum and maximum | 2.000 and 2.600 mm [observed] |
| how many flames lean each way, and the run lengths | 14 with the ring, 18 against it; runs 1..3, listed above [observed] |
| narrowest air gap between any two flames | 7.275 mm [observed] |
| disc radius | 79.70 mm [observed] |
| tile fan on one exact arc | 79.55 mm on all 24, `5_tile_bays_or_notches` 0 [observed] |
| constant orange margin | 0.70 mm at all 24 boundaries [observed] |
| counter | 10.0 x 7.0 x 4.5 mm, 30 of them, one solid [observed] |
| stations, lane inner radius | 74.0, 63.5, 53.0, 42.5, 32.0; 26.5 mm [observed] |
| outermost counter fully supported | 1.0 of the footprint [observed] |
| tallest flame tip, tip-to-disc | 96.700 mm, 1.2133 [observed] |
| envelope | 189.213 by 183.186 mm [observed] |
| flame length spread | 4.150 to 17.000 mm, ratio 4.096 [observed] |
| tall flames, a minority, unevenly spaced | 8 of 32, spacing 3, 5, 4, 3, 6, 4, 3, 4 [observed] |
| turn exponent, total turn, share in the inner half | 1.15; 37.13 to 43.24 degrees; 0.4506 [observed] |
| tip height in Z, root height | 3.312 to 4.202 mm; 5.4 mm [observed] |
| stack | 5.4 / 6.0 / 6.2, 2.2 mm tile on 3.8 mm of body [observed] |
| RULES.md carried byte for byte | sha256 `d601a858...1fd9d66` confirmed on the copied file [observed] |
| parts | 55 [observed] |

### Three disclosed engineering decisions

[assumed] **Thirty-two flames, not some other reduction.** The Wish fixes the
count. It is also the count at which a fat root and an open valley can both
exist: the concept's lick is roughly half as wide at its base as it is long,
the tallest flame here rises 17.0 mm, so its root wants about 8 mm, and [observed]
8 mm of root plus a valley as wide as a root needs a 15.6 mm pitch, which is [inferred]
360/32 of this circle.

[assumed] **The taper profile is reversed, not just re-exponented.** Lowering
the old `(1 - t) ** exp` exponent would have widened the flame at half length
but made it shed its width even faster at the root, which is the first half of
the defect. `1 - t ** exp` is the same one-parameter family run the other way:
flat at the root, steep at the cap. The flank arrives at the tip cap at about
30 degrees per side instead of the previous 2 degrees, which is what stops it
reading as a filament.

[assumed] **The corona ring starts half a valley past zero degrees.** The
plan used to put flame 0's root start exactly on the disc cylinder's own seam
at angle zero. Two vertices a femtometre apart then had to be merged, and the
kernel resolved that tie differently from run to run: the exported STEP
alternated between two byte orderings whose only difference was the last bit of
six coordinates. `_plan()` now begins the ring at half the closing valley, so
the seam falls in the middle of bare base circle. Six consecutive generations
of `part_sun_orange.step` now hash identically. This is a constant rotation of
the whole corona: no root arc, valley, rise, turn, cap, clearance or tip radius
changes, only each flame's absolute start angle and the envelope.

[assumed] **The tip cap still runs the other way from the length.** A 17 mm
lick ending in the widest cap reads as an oar; the mapping is squared, so only
the shortest nubs carry the 2.60 mm cap and the long licks spend most of their [observed]
length already near the 2.00 mm one. Every tip is still blunt and rounded off [observed]
and none of them terminates in an actual point.

## 4. Colour is a hard constraint

Five sealed sRGB values, authored as `Color(r, g, b)` with channels taken
directly from the hex the shop shows. Relative luminance, light to dark:
cream counter 0.9377, light lane 0.7410, body 0.5103, dark lane 0.2882, dark
brown counter 0.1741. [observed] Every neighbouring pair is at least 0.09
apart, the body sits between the two lane tones, and both counters sit outside
both lane tones. `validation.py` refuses to build if any of that stops holding,
and `measure/render_audit.py` reads the same five tones back out of
`snap/greyscale-top.png`. None of these values changed this round.

## 5. Printed in one colour each

Five filaments from the shop's stocked palette: `orange` body, `yellow` light
lane, `cocoa_brown` dark lane, `beige` and `dark_brown` counters. Every
occurrence name ends in the filament it prints in. All 55 parts print
flat-bottomed: the Sun underside down with material removed from every flame
top only, each tile top-face-down so its locating key points up, each counter
on its flat underside. [observed] No part needs support and none bridges. Mixed
handedness costs nothing here, because the mirror is a plan operation and every
flame flank stays vertical.

## 6. Negative requirements this design holds to

No fused skirt and no return to one poured rim; no closed loop, arch, ribbon or
handle anywhere on the part; no notch, scallop, bay or shortening cut into any
tile end and no change to the tile geometry at all; no flame material inside
the disc's edge circle; no adjacent roots touching; no valley that is a bare
stretch of base circle longer than either flame's own root; no flame root wider
than 55 per cent of its own root-to-root arc; no redesign of the approved flame
curve and no change to `CORONA_TURN_EXP` 1.15 or to the 37-44 degree turn; no
tip cap outside 2.00 to 2.60 mm and none widened past 2.60 mm; no tip shorter [observed]
in Z than 3.0 mm; [observed] no needle and no actual point; no strictly
alternating handedness and no handedness pattern that repeats round the ring;
no converging pair closer than 0.80 mm, and no flame shortened to buy that [observed]
clearance; no material taken off the underside of a flame; no flame top rounded
over or blended into its flanks; no flame detached from the body; no counter
landing on a flame, a marker or a fillet; no support taken away from a counter
at the outermost station; no wall below the checked minimum; no region needing
support and no bridge; no tall centre obstruction; no rails or walls; no
missing lane; no reduced lane capacity; no endpoint dots; no lane tone
colliding in value with either counter colour; no envelope above 194 mm; [observed]
[observed] no dice and no dice cups in the parts list; no printed randomiser
substituted for them; no edit to `RULES.md`.

## 7. Capacity, measured

Full 15-counter lane capacity is preserved and measured on the exact outlines:
five radial stations at 74.0, 63.5, 53.0, 42.5 and 32.0 mm [observed] and three
aligned 4.5 mm layers [observed] whose pitch equals the counter height, giving
tops at 6.0, 10.5 and 15.0 mm. [inferred] A counter clears its neighbour in the
same lane by 0.5 mm, [observed] the innermost clears the tile's inner edge by
0.5 mm [observed] and the outermost clears the tile's outer arc by 0.55 mm.
[observed] Worst own-tile support at the outermost station is 1.0 of the
footprint. [observed] Feasibility assert: `validation.py` refuses to build the
set unless the outermost counter fits inside `TILE_OUTER` and the innermost
inside `LANE_INNER`.

## 8. What still has to be measured, not assumed

Exact-solid support and clearance for all 24 lanes across five stations; the
crown's plan, its taper, its handedness and its ramp against every acceptance
clause above; the wall and overhang gates on every one of the 55 printable
entries; interference across the assembled set; and one independent blind
review of the canonical images that records unprimed observations first, is
asked directly whether the object reads as a sun or as a wheel, and only then
compares each correction requirement, including every negative one. No physical
handling, print success, tile retention, stack stability, durability, human
response or dice fairness is claimed. Motion is unverified: the set has no
coupled mechanism and the operator's frozen Make option disables motion checks.
