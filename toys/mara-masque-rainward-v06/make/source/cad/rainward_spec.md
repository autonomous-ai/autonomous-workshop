# Rainward Emberfan - CAD build spec

Correction of the unreleased Rainward Emberlick. Wish identity
`wish-20260918-160454-5822f76d`, Make subject
`66b77450b9525ed6a3588d3a2442f1f1cf7ee11f7dea609827600ae1faf16814`, selected
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
`9e27d8869393c93ab743f26a4a6ffe020b9aa941719bd154cfca465556ef1087`, and the
local clone under `revision-work/`: its `make/source/cad/` tree, its own
`rainward_spec.md`, `product/DESIGN.md`, the full `product/RULES.md`, its
`make/invented.json` and its archived renders.

[observed] Both sealed reference images were opened and measured. `ref-01`
(`wish-references/ref-01-idea-3-corona-rim.png`, copied to
`ref/concept-rim.png`) is the concept: a plain circular disc of 24 radial
lanes, teardrop counters in two tones, two player-supplied cups and two
player-supplied dice, and a rim of separate licks of flame with open background
between them and notches that cut down to the disc's own edge. `ref-02`
(`wish-references/ref-02-v8-rim-comparison.png`, copied to
`ref/previous-rim-comparison.png`) is the previous round's own unwrapped
comparison: one third of the ring, radius 0.86 to 1.22 of the disc, 1600 px
wide. Its lower strip is the fault this correction exists to fix - a rim whose
licks fuse at the root into one poured, wavy mass - and its two teardrop-shaped
holes are the hero arch's legs.

[observed] The clone's `product/RULES.md` is carried into this revision
byte-identical, sha256
`d601a858b70b4c1685dced91c7f176d73e4779a3ad784e9b13c7fc88d1fd9d66`.

[observed] The clone's sealed source tree is an earlier link in the correction
chain than the build this Wish describes: it carries a 90 mm disc, 38 fused [observed]
tongues, an 8.0 mm deck and 12 x 8 x 4 mm counters, where the Wish restates the [observed]
last build as a 79.70 mm disc, a 5.4 mm deck and 10 x 7 x 4.5 mm counters. The [observed]
Wish's own restated values govern; the clone supplies the construction, the
modules, the plan mathematics, the rule ledger, the counter outline and the
audit method, all of which are reused here.

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
  every boundary; [observed]
- five radial stations at 74.0, 63.5, 53.0, 42.5 and 32.0 mm with `LANE_INNER` [observed]
  26.5 mm, three aligned layers, full 15-counter lane capacity; [observed]
- setup A 24:2, 13:5, 8:3, 6:5 and B 1:2, 12:5, 17:3, 19:5; [observed]
- one counter silhouette at `DROP_L` 10.0 by `DROP_W` 7.0 by `DROP_H` 4.5 mm, [observed]
  the clone's original Bezier outline scaled to that plan, and all thirty
  counters the same solid; [observed]
- the `BAR_R` 24.0 mm centre bar, open and unobstructed, its top the highest [observed]
  plane on the board; [observed]
- the stack: `DECK` 5.4, `LANE_TOP` 6.0, `BAR_TOP` 6.2, `TILE_T` 2.2 mm of tile [observed]
  on `POCKET_FLOOR` 3.8 mm of solid body under the pocket; [observed]
- the tallest flame tip at `CORONA_MAX_R` 96.70 mm, a tip-to-disc ratio of [observed]
  1.2133 against the concept's 1.22, and an envelope under 194 mm; [observed]
- the flame curve the third blind critic named and approved: `CORONA_TURN_EXP`
  1.15, total turn 37 to 44 degrees root to tip, 0.4506 of it inside the inner
  half, every flame turning the same way; [observed]
- tip caps 2.60 to 4.10 mm across the plan, every tip at least 3.0 mm tall in [observed]
  Z, `CORONA_TOP` 5.4 mm at the root, one clean plane per flame top, material [observed]
  removed from the top only; [observed]
- flame lengths spanning more than four to one shortest to tallest, with the
  tall ones a quarter of the ring, unevenly spaced; [observed]
- three oranges - body #FF671F, light lane #FFB549, dark lane #8E3C06 - with
  the body between the two lane tones in greyscale, a cream counter lighter
  than both lane tones and a dark brown counter darker than both; [observed]
- 55 parts: one Sun board, 24 lane tiles, 30 counters. No dice, no dice
  cups. [observed]

## 3. The correction - two changes to the rim, and nothing else

### 3.1 Delete the hero arch

[observed] Four blind critics flagged the arched loop in every round of the
previous chain: spike tips passing through the handle ribbon with no boolean
cleanup, a tooth interpenetrating the arch, no pad or blend where the legs meet
the body, and both feet diving behind the tile plane without merging. Three
repair rounds never resolved it.

[assumed] It is removed outright rather than repaired. There is no `hero`
module, no `hero_profile`, no closed loop, no arch, no ribbon and no handle
anywhere in the plan or the solid; `measure/plan_audit.py` fails if any
callable whose name contains hero, arch, loop, ribbon or handle exists on the
plan surface, and if the body's plan carries any interior ring at all.
Measured: `1_closed_loops` 0, `1_hero_callables` empty. [observed]

[assumed] Where the arch stood, the rhythm simply continues: the 48 flames are
generated by one rule for the whole ring, so no angular window is treated
specially and there is no seam or gap at the old location.

### 3.2 Let the flames stand apart

[observed] The one round-four finding that measurement did not contradict is
the melted read - a rim that looks poured rather than cut. Its cause is the
zero-gap rule every brief since the second correction carried, which made
adjacent flame roots meet exactly. That rule is withdrawn here.

[assumed] The base is now the disc's own circular edge: `parts/body.py` builds
the deck as one plain cylinder of radius `SUN_R`, and every flame closes its
plan face on its own arc of that circle, so the flame lies wholly outside the
edge and the two meet along the arc alone. Between two flames the boundary is
that bare circle, 0.4 mm under the deck top where the rim ring carries the tile [observed]
lips, and open background above it.

[assumed] Root arcs and valleys are generated together so both of the Wish's
separation clauses hold by construction rather than by search. A valley is
0.940 to 0.995 of the smaller of the two roots it separates, which bounds the
root at 55 per cent of its own root-to-root arc from the other side.

Measured on the plan the CAD extrudes: [observed]

| clause | measured |
|---|---|
| root arc on the base circle | 5.104 to 5.622 mm [observed] |
| valley arc between two roots | 4.821 to 5.366 mm [observed] |
| widest valley over the smaller root beside it | 0.9941 |
| widest root over its own root-to-root arc | 0.5246 |
| narrowest air gap between two flames in plan | 4.821 mm [observed] |
| narrowest gap to a second neighbour | 14.879 mm [observed] |
| adjacent roots touching | none |
| separate pieces of body outside the edge circle, counted in the render | 48 |

The last row is measured from pixels, not parameters:
`measure/render_audit.py` masks the board in `snap/top.png`, keeps only what
lies outside radius `SUN_R` + 0.45 mm, and labels the connected regions. A rim [observed]
that was poured and set is one region. This one is 48, one per flame.

### 3.3 Measured against every acceptance clause

| Wish clause | measured |
|---|---|
| unwrapped comparison rebuilt, same window and arc | `snap/rim-comparison.png`, radius 0.86 to 1.22 of the disc, 120 degrees, 1600 px |
| root width and valley for every flame, as a ratio | `measure/plan-audit.json`, key `2_flame_table`, 48 rows |
| no closed loop, arch, ribbon or handle | 0 interior rings, 0 such callables |
| disc radius | 79.70 mm [observed] |
| tile fan on one exact arc | 79.55 mm on all 24, `3_tile_bays_or_notches` 0 [observed] |
| constant orange margin | 0.70 mm at all 24 boundaries [observed] |
| counter | 10.0 x 7.0 x 4.5 mm, 30 of them, one solid [observed] |
| stations, lane inner radius | 74.0, 63.5, 53.0, 42.5, 32.0; 26.5 mm [observed] |
| outermost counter fully supported | 1.0 of the footprint |
| tallest flame tip, tip-to-disc | 96.70 mm, 1.2133 [observed] |
| envelope | 186.715 by 188.500 mm [observed] |
| flame length spread | 4.15 to 17.00 mm, ratio 4.096 [observed] |
| tall flames, a minority, unevenly spaced | 12 of 48, spacing 3, 5, 4, 3, 6, 4, 3, 5, 4, 3, 4, 4 |
| turn exponent, total turn, share in the inner half | 1.15; 37.13 to 43.78 degrees; 0.4506 |
| tip caps across the plan | 2.60 to 4.10 mm [observed] |
| tip height in Z, root height | 3.243 to 4.202 mm; 5.4 mm [observed] |
| stack | 5.4 / 6.0 / 6.2, 2.2 mm tile on 3.8 mm of body [observed] |
| greyscale separability | order holds, smallest gap 0.102 in the render |
| parts | 55 |

### Three disclosed engineering decisions

[assumed] **Forty-eight flames.** The Wish fixes no count. Forty-eight puts the
mean root-to-root arc at 10.43 mm, which is the largest count whose roots still [observed]
clear the 0.70 mm margin rule and whose valleys stay under their own roots, [observed]
and it is the density the concept image reads at.

[assumed] **The tip cap runs the other way from the length.** A 17 mm lick
ending in the widest 4.10 mm cap reads as an oar; the mapping is squared, so [observed]
only the shortest nubs carry the widest cap and the long licks spend most of
their length near the 2.60 mm one. Every tip is still blunt and rounded off and [observed]
none of them terminates in an actual point.

[assumed] **The bank markers moved to the centre bar.** The constant 0.70 mm
orange margin leaves no boundary wide enough to carry the clone's raised
capsule out among the lanes, and a 0.70 mm fin standing 0.8 mm proud would be a [observed]
wall under the checked minimum. A first attempt put four raised dashes on the
hub ring; an independent blind critic read them as "small hook-shaped slivers
and notches ... unclosed or overshooting geometry". They are therefore cut, not
raised, and they sit on the centre bar's own top face: four radial V grooves,
`MARKER_W` 2.0 mm across the mouth, `MARKER_L` 6.4 mm long, `MARKER_DEPTH` [observed]
0.7 mm deep, reaching out to `MARKER_OUTER` 23.4 mm inside the `BAR_R` 24.0 mm [observed]
bar. The bar stays a flat unobstructed landing: a 10.0 mm drop bridges a 2.0 mm [observed]
groove, a ratio of 5.0, and no tick lies under any of the six bar sites. The [observed]
feature and its function - marking the 24/1, 6/7, 12/13 and 18/19 bank
boundaries - are preserved; only its place changed, and that change is forced
by a value the Wish itself fixes.

## 4. Colour is a hard constraint

Five sealed sRGB values, authored as `Color(r, g, b)` with channels taken
directly from the hex the shop shows. Relative luminance, light to dark:
cream counter 0.9377, light lane 0.7410, body 0.5103, dark lane 0.2882, dark
brown counter 0.1741. [observed] Every neighbouring pair is at least 0.09
apart, the body sits between the two lane tones, and both counters sit outside
both lane tones. `validation.py` refuses to build if any of that stops holding,
and `measure/render_audit.py` reads the same five tones back out of
`snap/greyscale-top.png`, where the smallest gap measures 0.102. [observed]

## 5. Printed in one colour each

Five filaments from the shop's stocked palette: `orange` body, `yellow` light
lane, `cocoa_brown` dark lane, `beige` and `dark_brown` counters. Every
occurrence name ends in the filament it prints in. All 55 parts print
flat-bottomed: the Sun underside down with material removed from every flame
top only, each tile top-face-down so its locating key points up, each counter
on its flat underside. [observed] No part needs support and none bridges.

## 6. Negative requirements this design holds to

No closed loop, arch, ribbon or handle anywhere on the part; no notch, scallop,
bay or shortening cut into any tile end; no flame material inside the disc's
edge circle; no adjacent roots touching; no valley that is a bare stretch of
base circle longer than either flame's own root; no flame root wider than 55
per cent of its own root-to-root arc; no redesign of the approved flame curve
and no change to `CORONA_TURN_EXP` 1.15; no tip cap outside 2.60 to 4.10 mm and [observed]
no tip shorter in Z than 3.0 mm; [observed] no needle and no actual point; no
material taken off the underside of a flame; no flame top rounded over or
blended into its flanks; no flame detached from the body; no plain stretch of
disc edge left bare beyond the stated bound; no counter landing on a flame, a
marker or a fillet; no support taken away from a counter at the outermost
station; no wall below the checked minimum; no region needing support and no
bridge; no tall centre obstruction; no rails or walls; no missing lane; no
reduced lane capacity; no endpoint dots; no lane tone colliding in value with
either counter colour; no envelope above 194 mm; [observed] no dice and no dice
cups in the parts list; no printed randomiser substituted for them; no edit to
`RULES.md`.

## 7. Capacity, measured

Full 15-counter lane capacity is preserved and measured on the exact outlines:
five radial stations at 74.0, 63.5, 53.0, 42.5 and 32.0 mm [observed] and three
aligned 4.5 mm layers [observed] whose pitch equals the counter height, giving
tops at 6.0, 10.5 and 15.0 mm. [inferred] A counter clears its neighbour in the
same lane by 0.5 mm, [observed] the innermost clears the tile's inner edge by
0.5 mm [observed] and the outermost clears the tile's outer arc by 0.55 mm.
[observed] Worst own-tile support at the outermost station is 1.0 of the
footprint - the whole counter lands on its own tile, with no part of it past
the tile edge. [observed] Feasibility assert: `validation.py` refuses to build
the set unless the outermost counter fits inside `TILE_OUTER` and the innermost
inside `LANE_INNER`, so a station table that cannot seat its counters stops the
build instead of reaching a render.

## 8. What still has to be measured, not assumed

Exact-solid support and clearance for all 24 lanes across five stations; the
crown's plan and its ramp against every acceptance clause above; the wall and
overhang gates on every one of the 55 printable entries; interference across
the assembled set; and one independent blind review of the canonical images
that records unprimed observations first and only then compares each correction
requirement, including every negative one. No physical handling, print success,
tile retention, stack stability, durability, human response or dice fairness is
claimed. Motion is unverified: the set has no coupled mechanism and the
operator's frozen Make option disables motion checks.
