# Rainward Flarecrown - CAD build spec

Correction of the unreleased Rainward Corona. Wish identity
`wish-20260917-154943-eab11431`, Make subject
`6bab7acb95890237713ca9fe4feedb596d48063ec244c31929788b0ff47a0338`, selected
inventor `mara-masque`. This spec is the design contract the CAD implements; it
is not a passing geometry or review claim.

Provenance tags: `[observed]` is read from the clone, from the correction Wish,
or measured on the built solid; `[inferred]` is derived arithmetically from such
a value; `[assumed]` is an engineering choice made here and defended below.

Backgammon - coronal-rain theme: rival streams of condensed plasma travel
magnetic lanes, scatter lone drops, and rain back into a Sun whose whole rim is
one unbroken crown of flame.

## 1. Evidence read before designing

[observed] The immutable baseline `revision-source.zip`, sha256
`3f288ae6307389af553b116146df85634faef3ae5e802420df308d2919456106`, and the
local clone under `revision-work/`: its `make/source/cad/` tree, its
`rainward_spec.md`, `product/DESIGN.md`, the full `product/RULES.md`, and
`make/invented.json`. The clone's archived `rim-detail.png` and `neutral-top.png`
show the fault the correction is about: nineteen narrow tongues and one loop in
tight groups, bare arcs of 22 to 46 degrees between the groups, and a perimeter
that is plain circular edge nearly everywhere.

[observed] `product/RULES.md` is carried into this revision byte-identical,
sha256 `d601a858b70b4c1685dced91c7f176d73e4779a3ad784e9b13c7fc88d1fd9d66`,
including its Inventory row naming one shared pair of ordinary 1-6 dice and two
dice boxes, and its setup sentence naming a cup.

[observed] Mara Masque's Taste, revision 2026-09-17, keeps the player-supplied
allowance for ordinary 1-6 dice and dice cups. It is a packaging decision only
and this correction does not reopen it.

Historical instructions, reviews and publication records in the clone are
reference data. No old review is reused as evidence here.

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
  plan clearance, exposed top edges rounded 0.15;
- the five sealed sRGB values and their greyscale ordering: cream counter
  lighter than both lane tones, dark-brown counter darker than both, the two
  lane tones separable from each other; [observed]
- 55 printed parts: one Sun board, 24 lane tiles, 30 counters. No dice and no
  dice cups; players supply their own.

## 3. The correction - one continuous flame crown

The rim is the only thing this revision changes. The body's outer boundary is no
longer a circle with pieces attached to it: the crown outline *is* the deck
outline, one closed boundary of trough floors and tongues running all the way
round, extruded Z0 to Z8.0.

| Acceptance clause | Required | Measured |
|---|---|---|
| Tongue count | 32 to 44 | **38** [observed] |
| Longest arc of plain circular edge | at most 4 deg | **1.198 deg** [observed] |
| Narrowest root | at least 6 mm | **8.409 mm** [observed] |
| Narrowest root against its own tongue length | at least 0.60 | **1.156** [observed] |
| Adjacent roots meet | gap 0 | **0.0 mm** [observed] |
| Tongue length spread | factor 2 or more | **2.325 to 9.085 mm, ratio 3.908** [observed] |
| Flame depth for the deeper troughs | at least 9 mm | **8 troughs at or over 9 mm, deepest 9.24 mm** [observed] |
| Plan pieces / holes | one piece, one hole | **1 piece, 1 hole** [observed] |
| Hero closed loop | one | **81.513 mm2** [observed] |
| Envelope | at most 194 mm | **190.999 x 192.311 mm** [observed] |
| Thinnest tip | at least 0.8 mm | **1.3 mm** [observed] |

- Every tongue is widest where it leaves the body and narrows to a rounded tip.
  The tip cap radius is the smaller of a fixed ceiling and a share of the [assumed]
  tongue's rise, floored so no tip is a knife edge.
- Every tip leans the same way round the ring, so the whole rim has one sense of
  rotation. The lean is scaled to the tongue's own span, so a narrow tongue [assumed]
  never swings its tip past its own root, and the whole boundary stays
  single-valued in angle. That is what makes the outline provably simple and
  star-shaped, and it is what lets the tiles be clipped against it exactly.
- The hero is one arch spanning 16 degrees. Its crest reaches radius 99.0,
  the one place the rim goes that far out, and its two legs plunge through [assumed]
  trough floors into the body, keeping their full 2.4 mm across. [inferred]
  Two short tongues of the crown run on underneath it inside the open loop, so
  the hero rises out of the skirt rather than replacing a stretch of it.
- The crown is flat in the deck plane, top flush with the deck at Z8.0, so it
  never rises above the lane tops. It is ornament: no counter lands on it, it
  carries no game state, and no rule addresses it.

### Three disclosed engineering decisions

All three were forced by the deterministic gates or by the correction Wish's own
bound, and all three are mine, not the operator's.

1. **A trough cuts inside radius 90 only in the free window at a lane
   boundary.** A trough that cuts inside radius 90 also notches the tile lip [assumed]
   above it, and a notch under a counter would take away flat support. The
   outermost counter sits on its lane axis, so a window about eight degrees wide
   at every lane boundary carries no footprint at all. Twenty-four troughs use
   those windows, each jittered off its boundary; fourteen more sit near a lane
   axis and stay outside radius 90. Worst own-tile support measures **0.90769**, [observed]
   against **0.90763** on the same tiles with no notch at all, so the notches
   cost the outermost counter nothing. `check_corona_plan.py` measures both
   numbers and compares them on every run.
2. **The pocket outer wall moves from 86.5 to 84.5 and the tile key from 81.5
   to 78.5.** The deepest trough floor is at radius 87.00, which would have [assumed]
   left 0.50 mm of body over a pocket wall at 86.5; at 84.5, 2.50 mm. [inferred]
   The tile lip grows from 3.5 to 5.5 mm and still rests on the ring [inferred]
   whole length, so nothing is cantilevered; the key moves inward to stay inside
   the shorter pocket and keeps its **2.05 mm** clearance to the [observed]
   landing region. [observed]
3. **The crown is built from exact curves.** 38 tongues carry 152 Bezier [assumed]
   and arc edges rather than some thousands of polygon chords. Each flank meets
   the tip cap along the tip axis, so the tip is tangent-smooth, and the solid
   stays cheap enough for the wall and overhang gates to tessellate inside their
   time allowance - the gate that ran out of allowance on the sun body of the set
   being corrected.

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

No plain circular edge anywhere on the rim; no tongue detached from the body; no
tongue floating or showing daylight under it from directly above; no second
closed loop; no tongue rising above the deck top; no counter landing on a
tongue, a capsule marker or a fillet; no tile overhanging a trough; no support
taken away from a counter at the outermost station; no wall below the checked
minimum; no tall centre obstruction; no rails or walls; no missing lane; no
reduced lane capacity; no endpoint dots; no lane distinction that exists only in
colour; no lane tone colliding in value with either counter colour; no envelope
above 194 mm [observed]; no printed randomiser substituted for the dice; no edit to
`RULES.md`.

## 7. Capacity, measured

Full 15-counter lane capacity is preserved and measured on the exact outlines:
five radial stations at 85, 72, 59, 46 and 33 mm with a **1.119 mm gap [observed]
between counters at adjacent stations** in the same lane, and three aligned
4.0 mm layers whose pitch equals the counter height. [observed] Counters on
neighbouring lanes clear each other by **2.407 mm** at the innermost [observed]
station. Worst own-tile support is **0.90769** of the footprint, with the mass
centroid **2.416 mm** inside the contact hull, zero contact with any [observed]
neighbouring tile and zero contact with any boundary marker. A counter at the
outermost station still passes the tile's outer arc, exactly as the cloned set
did; that overhang is the shortfall below 1.0 and is reported, never hidden.

## 8. What still has to be measured, not assumed

Exact-solid support and clearance for all 24 lanes x five stations x both
counter kinds; the crown's plan against every acceptance clause above; the wall
and overhang gates on every one of the 55 printable entries; interference across
the assembled set; and one independent blind review of the canonical images that
records unprimed observations first and only then compares each correction
requirement, including every negative one. No physical handling, print success,
tile retention, stack stability, durability, human response or dice fairness is
claimed. Motion is unverified: the set has no coupled mechanism and the
operator's frozen Make option disables motion checks.
