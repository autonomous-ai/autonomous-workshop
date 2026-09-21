# Rainward Bladefire - CAD build spec

Correction of the unreleased Rainward Flarecrown. Wish identity
`wish-20260918-014828-b8fc431a`, Make subject
`b907183bb1b5ca1967587a29e1f865f4ba29105e645e298ffce2475496b013ec`, selected
inventor `mara-masque`. This spec is the design contract the CAD implements; it
is not a passing geometry or review claim.

Provenance tags: `[observed]` is read from the clone, from the correction Wish,
or measured on the built solid; `[inferred]` is derived arithmetically from such
a value; `[assumed]` is an engineering choice made here and defended below.

Backgammon - coronal-rain theme: rival streams of condensed plasma travel
magnetic lanes, scatter lone drops, and rain back into a Sun whose rim is a
crown of curled flame laid back off the disc.

## 1. Evidence read before designing

[observed] The immutable baseline `revision-source.zip`, sha256
`e386969c196515ba13e569954f1634ad64cee9656a2e39edcd49145053cdb909`, and the
local clone under `revision-work/`: its `make/source/cad/` tree, its
`rainward_spec.md`, `product/DESIGN.md`, the full `product/RULES.md`, its
`make/invented.json`, and its archived `top.png`, `iso.png` and `rim-detail.png`.

[observed] Those archived renders show both faults the correction is about.
Every tongue is a broad flat triangle extruded to the full 8 mm [observed] deck
height with a vertical wall all the way round, so the rim reads as a cog or the
crimped edge
of a bottle cap. And the tiles are bayed and clipped: the fan of 24 tiles no
longer finishes on a circle, every tile end is bitten, and the board stops
reading as one piece.

[observed] `product/RULES.md` is carried into this revision byte-identical,
sha256 `d601a858b70b4c1685dced91c7f176d73e4779a3ad784e9b13c7fc88d1fd9d66`.

[observed] Mara Masque's Taste keeps the player-supplied allowance for ordinary
1-6 dice and dice cups. It is a packaging decision only and this correction does
not reopen it.

Historical instructions, reviews, reports and publication records in the clone
are reference data, never current authority. No old review is reused as
evidence here, and this revision does not update the original publication.

## 2. Preserved contract

Unchanged from the set being corrected, and asserted in `validation.py` or
measured in `measure/`:

- the ordinary 1911 Backgammon rules exactly as `RULES.md` states them, with no
  rule, power, component, endpoint dot or subsystem added;
- 24 lanes, four banks of six, lane axes `-75 + 15(p-1)` degrees; [observed]
- five radial stations at 85, 72, 59, 46 and 33 mm, three aligned layers, [observed]
  full 15-counter lane capacity;
- setup A 24:2, 13:5, 8:3, 6:5 and B 1:2, 12:5, 17:3, 19:5; [observed]
- both counter silhouettes at 12 x 8 x 4 mm, original Bezier points; [observed]
- the radius-24 centre bar with its six 12 x 8 support positions at x = -12, 0,
  12 and y = -5, +5, open and unobstructed; [observed]
- four short rounded capsule markers, 10 x 0.8 mm at radius 65, on the [observed]
  24/1, 6/7, 12/13 and 18/19 boundaries;
- 0.8 mm of exposed body at ordinary boundaries, 1.6 mm at a bank; [observed]
- deck top 8.0, lane tops 8.8, centre bar top 9.0, overall Sun height 9.0;
- 24 separate lane tiles, twelve yellow and twelve cocoa brown, strictly
  alternating, 2.8 mm thick on a 6.0 pocket floor, 0.15 mm per side of [observed]
  plan clearance, exposed top edges rounded 0.15, outer radius 89.85;
- the skirt's 38 troughs and 38 tip radii, byte for byte the table the [observed]
  clone carried, so tongue count, root widths, root joins, length spread and
  flame depth are all arithmetically unchanged;
- the hero arch, its 18 degree span, its radius-99.0 crest and its one [observed]
  closed loop;
- the five sealed sRGB values and their greyscale ordering: cream counter
  lighter than both lane tones, dark-brown counter darker than both, the two
  lane tones separable from each other; [observed]
- 55 printed parts: one Sun board, 24 lane tiles, 30 counters. No dice and no
  dice cups; players supply their own.

## 3. The correction - two changes to the tongues, and the tiles put back

### 3.1 Taper early and turn through the outer half

A tongue is no longer a triangle stretched between its two root points. It is a
swept blade. Its spine leaves the root chord along that chord's outward [assumed]
normal and turns steadily one way; the heading follows `turn * t**2.4`, so four
fifths of the whole turn happens in the outer half of the blade rather than
the tongue leaning over as a whole. The half width over the tip falls as
`(1 - t)**4.2`, which takes the width off at once where the tongue leaves its
trough - that is what makes the notch between two tongues a V rather than a
scallop - and leaves the outer half already slender.

### 3.2 Bring the top down as the tongue runs outward

Each tongue is built as its own flat-bottomed solid and fused onto the [assumed]
root chord it shares with the deck core. One plane per tongue then takes the top
down. The plane passes through the deck height at the tongue's own root chord and
falls in a straight line from there to that tongue's own tip height, so the ramp
is the whole blade rather than a short bevel on a full-height wall. A rim collar
puts the body back up to the ring top out to radius 90 [inferred], clipped to the
skirt plan, so every tile lip still rests on a continuous ring. Material comes off the top only: the underside stays
flat on the bed, the flanks stay vertical, and the ramp meets each flank along
one straight crisp edge. Nothing is rounded over and no surface is blended into
a flank, so no tongue can read as a drip of wax slumped over the edge.

Tip heights are dealt out against how far each tongue actually [assumed]
reaches, longest lowest, with a jittered quarter mixed in, so the crown lies
back at one attitude instead of a few stubs dropping off a cliff.

### 3.3 The 24 lane tiles are put back on one circle

The previous correction's tile bays and trough clipping are withdrawn entirely.
Every tile's outer edge is one exact circular arc of radius 89.85 centred [observed]
on the board - the same arc on all 24 - so the fan closes on a single
continuous circle. Nothing is notched, scalloped or bayed out of a tile end, no
tile is shortened, no radius is changed and no tile plan is altered in any other
way. No orange flame root is visible inside the disc: the flame lives entirely
outside that arc.

### 3.4 Measured against every acceptance clause

| Acceptance clause | Required | Measured |
|---|---|---|
| Tip tangent against root tangent | 25 to 45 deg, every tongue | **37.41 to 43.22 deg** [observed] |
| Turn inside the outer half alone | at least 20 deg | **29.91 to 34.56 deg** [observed] |
| Outer half slender against the root | mid width under half the root | **0.268 at worst** [observed] |
| All tongues turn the same way | one sense | **one sense** [observed] |
| Tip height in Z | 3.5 to 5.0 mm, varying | **3.579 to 4.238 mm, 38 distinct** [observed] |
| Root height in Z | 8.0 mm | **8.0 mm** [observed] |
| Top is one clean ramp | one plane per tongue | **one plane, 24.9 to 58.5 deg** [observed] |
| Tip plan thickness | at least 1.3 mm | **1.50 mm** [observed] |
| Tile fan outer boundary | one continuous circular arc | **one arc, radius 89.85 on all 24** [observed] |
| Tile bays, notches or scallops | none | **0** [observed] |
| Tongue count | 32 to 44 | **38** [observed] |
| Narrowest root | at least 6 mm | **8.409 mm** [observed] |
| Narrowest root against its own tongue length | at least 0.60 | **1.156** [observed] |
| Adjacent roots meet | gap 0 | **0.0 mm** [observed] |
| Tongue length spread | factor 2 or more | **2.325 to 9.085 mm, ratio 3.908** [observed] |
| Flame depth for the deeper troughs | at least 9 mm | **8 troughs at or over 9 mm, deepest 9.24 mm** [observed] |
| Plan pieces / holes | one piece, one hole | **1 piece, 1 hole** [observed] |
| Hero closed loop | one | **91.723 mm2** [observed] |
| Envelope | at most 194 mm | **191.105 x 192.514 mm** [observed] |
| Outermost counter support | at least 0.90769 | **0.90769** [observed] |
| Longest arc of plain circular edge | at most 4 deg | **1.317 deg** [observed] |
| Longest run of that band that is also tangential | - | **0.088 deg** [observed] |

### Four disclosed engineering decisions

All four are mine, not the operator's.

1. **The plain-circular-edge proxy rose from 1.198 to 1.317 degrees.** [observed]
   That figure counts the longest angular run of boundary lying within 0.5 mm [assumed]
   of radius 90, at the sampling density the clone's own audit used. It rose
   because a curling flank now sweeps across that radius instead of crossing it
   head on; it is not a circular edge that reappeared. `check_corona_plan.py`
   therefore also reports the run that is within the band *and* within 15
   degrees of tangential - which is what a plain circular edge actually is -
   and that measures **0.088 degrees**. The rim carries no bare arc [observed]
   anywhere. The contract limit is 4 degrees and both numbers are inside it.
2. **A tile lip laps up to 2.75 mm past the body ring at the deepest [observed]
   troughs.** Every tile ends on the same circle, so where a trough floor cuts
   inside radius 89.85 the outer corner of that tile's 1.0 mm [inferred] lip reaches over
   the notch. It is a corner tab a few millimetres across on a part that prints
   flat and alone, so it costs no printed overhang and no support; it is
   reported here rather than fixed by cutting the tile, because cutting the
   tile is exactly what this correction forbids. Every deep trough still sits
   in the free window at a lane boundary, so no counter at the outermost
   station loses any support: that measures **0.90769**, the figure the [observed]
   Wish requires it to hold.
3. **The crown and the tiles are built from exact curves.** Each flank is [assumed]
   a short chain of cubic Beziers fitted to the analytic blade to within
   **0.048 mm**, each tip cap is one arc, and each tile is two lines [observed]
   and two exact arcs instead of forty chords. That is what took the Sun part
   from 11.7 MB to **6.9 MB** and the assembled export from 48.3 MB to
   **9.2 MB**. The Sun part misses the Wish's 4 MB target; the [observed]
   remaining bulk is the hero arch's 280-sample plan, which is preserved
   geometry this correction is not allowed to touch. The sealed archive is far
   inside its 128 MiB limit either way.
4. **The fall starts at the root chord, and a rim collar carries the [assumed]
   tile lips.** The first repaired build held the deck height out to radius 90
   and only then fell, which left a short steep bevel on top of a full-height
   wall; the independent critic read that rim as a crimped bottle-cap crown,
   the exact fault being corrected. Starting the fall at the root chord makes
   the ramp the face the eye sees, but on its own it would drop the body top
   under the outer millimetres of every tile lip. `rim_collar()` restores the
   body to the ring top across the band the lips occupy, clipped to the skirt
   plan so no trough is filled in, which keeps the lip carried and the flame
   laid back at the same time.

## 4. Colour is a hard constraint

Five sealed sRGB values, light to dark, with their Rec.709 greyscale:

| Value | sRGB | Greyscale | Filament |
|---|---|---:|---|
| Cream counter | 0.97, 0.94, 0.82 | 0.938 | `beige` |
| Light lane tone | 1.00, 0.83, 0.10 | 0.813 | `yellow` |
| Sun body | 1.00, 0.66, 0.18 | 0.698 | `orange` |
| Dark lane tone | 0.60, 0.39, 0.20 | 0.421 | `cocoa_brown` |
| Dark-brown counter | 0.24, 0.16, 0.12 | 0.174 | `dark_brown` |

One lane tone is clearly lighter than the body and the other clearly darker;
both stay between the two counter values, so neither counter ever sits on a tile
close to its own value. `measure/check_tone.py` re-measures this on the
canonical top render converted to greyscale, because the renderer applies its
own lighting.

## 5. Printed in one colour

`snap/neutral-board-top.png` is the single-material top view.
`measure/check_countability.py` samples it: 24 boundaries at uniform 15 degree
spacing, the four widest at 7.5, 97.5, 187.5 and 277.5 degrees.

## 6. Negative requirements this design holds to

No notch, scallop, bay or shortening cut into any tile end; no change to any
tile's radius, outline, lapping lip, clearance or plan; no visible orange flame
root inside the disc; no flame material inside the tile edge; no tongue top
rounded over or blended into its flanks; no material taken off the underside of
a tongue; no tongue thinner in plan than 1.3 mm [observed]
and no tongue tip shorter in Z than 3.0 mm [observed]; no
needle and no spike; no plain circular edge anywhere on the rim; no tongue
detached from the body; no second closed loop; no tongue rising above the deck
top; no counter landing on a tongue, a capsule marker or a fillet; no support
taken away from a counter at the outermost station; no wall below the checked
minimum; no region needing support and no bridge; no tall centre obstruction; no
rails or walls; no missing lane; no reduced lane capacity; no endpoint dots; no
lane distinction that exists only in colour; no lane tone colliding in value
with either counter colour; no envelope above 194 mm [observed]; no printed
randomiser substituted for the dice; no edit to `RULES.md`.

## 7. Capacity, measured

Full 15-counter lane capacity is preserved and measured on the exact outlines:
five radial stations at 85, 72, 59, 46 and 33 mm [observed], and three aligned 4.0 mm [observed]
layers whose pitch equals the counter height. [observed] Counters on
neighbouring lanes clear each other by **2.407 mm** at the innermost [observed]
station. Worst own-tile support is **0.90769** of the footprint, with the mass
centroid **2.416 mm** inside the contact hull, zero contact with any [observed]
neighbouring tile and zero contact with any boundary marker. A counter at the
outermost station still passes the tile's outer arc, exactly as the cloned set
did; that overhang is the shortfall below 1.0 and is reported, never hidden.

## 8. What still has to be measured, not assumed

Exact-solid support and clearance for all 24 lanes x five stations x both
counter kinds; the crown's plan and ramp against every acceptance clause above;
the wall and overhang gates on every one of the 55 printable entries;
interference across the assembled set; and one independent blind review of the
canonical images that records unprimed observations first and only then compares
each correction requirement, including every negative one. No physical handling,
print success, tile retention, stack stability, durability, human response or
dice fairness is claimed. Motion is unverified: the set has no coupled mechanism
and the operator's frozen Make option disables motion checks.
