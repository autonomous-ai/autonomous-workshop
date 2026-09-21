# Rainward Bladefire

**What is in the box: the Sun board, its 24 lane tiles and 30 counters. No dice
and no dice cups are included.** Each player supplies one ordinary six-sided
die cup, and the pair shares two ordinary 1-6 dice of any standard make. Match
this specification: two cubic dice, faces 1 through 6, with the standard
opposite pairs 1-6, 2-5 and 3-4, of a size that throws freely on a table. Two
ordinary cups of the kind sold with any backgammon set will do. The game's
randomness is exactly those two dice; nothing printed here replaces them.

A Sun-shaped backgammon set. Twenty-four lanes alternate between two filament
tones around a 190 mm disc that stands 9 mm tall, the fan of tiles closes on one
clean circle, and outside that circle the rim is a crown of curled flame laid
back off the disc. This revision of Rainward Flarecrown preserves that set's
rules, lane topology, counter silhouettes, board plan, tile plan and heights,
and changes two things: the shape of the flame tongues, and the tile ends, which
go back to one continuous arc.

## Components

| Part | Count | Colour |
|---|---:|---|
| Sun body | 1 | orange |
| Lane tiles, odd-numbered points | 12 | yellow |
| Lane tiles, even-numbered points | 12 | cocoa brown |
| Single-tail counters | 15 | beige |
| Split-tail counters | 15 | dark brown |

55 printed parts. The two dice and the two cups are supplied by the players and
are not printed. The rules document still lists them with their unchanged
function and quantity, because this is a packaging decision and not a rules
change.

## Setting up and playing

Read [RULES.md](RULES.md) for the unchanged historical rules, setup and
orientation. That document keeps its original title and its exact original
text, including the inventory row that names one shared pair of ordinary 1-6
dice and two dice boxes. Nothing in it was edited to match the reduced box.

Each lane holds fifteen counters as five radial positions with three aligned
layers. Keep tails toward the centre and set each counter flat on its lane
tile. The four short rounded markers sit in the four wider boundaries and
separate the groups of six; they are not playing positions. The centre circle
is the capture bar.

## The flame crown

The rim is one continuous band of material. 38 tongues run round the disc. Each
one keeps the full width of the root it shares with both neighbours, sheds that
width early, curls one way as it runs out, and lies back: its top starts flush
with the deck and falls in one straight ramp to a low tip. The notches between
tongues are V and U troughs cut into that band, not gaps of air between separate
pieces. Measured on the exact plan the CAD extrudes and the exact plane each top
is cut by:

| What the rim has to do | Measured |
|---|---|
| Tip tangent differs from root tangent by 25 to 45 degrees | 37.41 to 43.22 degrees, every tongue |
| At least 20 degrees of that turn inside the outer half alone | 29.91 to 34.56 degrees |
| All tongues turn the same way round the ring | one sense |
| Width off early: mid length under half the root | 0.268 at worst |
| Tip height in Z between 3.5 and 5.0 mm, varying | 3.579 to 4.238 mm, 38 distinct values |
| Root height in Z | 8.0 mm, flush with the deck |
| The top is one clean ramp with crisp flank edges | one plane per tongue, 24.9 to 58.5 degrees |
| Tip at least 1.3 mm across in plan, 3.0 mm tall in Z | 1.50 mm across, 3.579 mm tall |
| Between 32 and 44 tongues | 38 |
| No arc of plain circular edge over 4 degrees | 1.317 degrees, of which 0.088 is tangential |
| Every root at least 6 mm and at least 60 percent of its own tongue length | 8.409 mm, 1.156 of length |
| Adjacent roots meet | join gap 0.0 mm |
| Lengths varying by a factor of two | 2.325 to 9.085 mm, ratio 3.908 |
| Flame depth at least 9 mm for the deeper troughs | 8 troughs at or over 9 mm, deepest 9.24 mm |
| Nothing floating | the plan is one piece with one hole |
| One closed loop that leaves the rim and rejoins it | 91.723 mm2, with the crown still running underneath it |

Material comes off the top of a tongue only. Every underside is flat on the bed,
so nothing cantilevers over air: the overhang gate reports zero regions needing
support and zero bridges on all 55 parts.

The hero is one arch near the lower rim. Its two legs plunge through trough
floors into the body, its crest is the one place the rim reaches radius
99.0 mm, and two short tongues of the crown run on underneath it inside the
open loop.

## Assembling the board

The 24 lane tiles drop into shallow pockets in the Sun body. Each tile is
2.8 mm thick and seats on a pocket floor 6.0 mm above the table, so its top
face finishes 8.8 mm up and stands 0.8 mm proud of the body around it. The plan
clearance is 0.15 mm per side at the pocket opening. One radial locating key on
each tile's underside drops into a matching recess in the pocket floor, so a
seated tile cannot turn or creep. Tiles are gravity-seated; no retention force
is claimed and none has been tested.

Every tile ends on the same exact circular arc at radius 89.85 mm, so the fan of
24 closes on one continuous circle and the board reads as a single object.
Nothing is notched, scalloped or bayed out of a tile end. The outer part of each
tile is a 1.0 mm lip that laps a continuous ring of body at the rim. Where one of
the deeper troughs cuts inside that circle, the outer corner of the lip above it
reaches up to 2.75 mm past the ring - a small corner tab, on a part that prints
flat and alone. Every deep trough sits in the free window at a lane boundary, so
the tile top is still one flat face all the way out wherever a counter lands: the
worst own-tile support under a counter measures 0.90769.

## Reading the board

The board body is a mid sun-orange. One lane tone is clearly lighter than it
and the other clearly darker, and both stay between the two counter colours, so
a cream counter always reads lighter than the tile under it and a dark-brown
counter always reads darker. `cad/measure/greyscale-tone.json` records that
check made on the canonical top render converted to greyscale.

The set also reads printed in one colour. Lane count, lane boundaries and the
four banks come from geometry: 0.8 mm of exposed body between ordinary lanes,
1.6 mm at the four bank boundaries, each tile standing 0.8 mm proud, and the
four short capsule markers. `cad/snap/neutral-board-top.png` is that
single-material view. `cad/measure/neutral-countability.json` counts the 24
boundaries and the four wide ones in it.

## Dimensions

Sun board 190 x 190 mm in plan with the flame crown reaching 191.105 x
192.514 mm, 9.0 mm tall overall. Deck top 8.0 mm, lane tile tops 8.8 mm, centre
bar top 9.0 mm, boundary markers to a maximum of 9.0 mm. Counter undersides
stack at 8.8, 12.8 and 16.8 mm. Counters are 12 x 8 x 4 mm. A tongue starts
flush with the deck at 8.0 mm and never rises above it, then falls to between
3.579 and 4.238 mm at its tip. Tongues reach 2.325 to 9.085 mm beyond their own
trough floors and the thinnest tip measures 1.50 mm across.

## Printing

Each production solid is under `parts/`. The editable source, the per-part STEP
files, the canonical images and the current measurements are under `cad/`.
`assembled.step` is the complete displayed set; print the separate components
rather than that layout. The declared digital verification conditions are a
200 x 200 x 200 mm bed and a 0.4 mm nozzle. The minimum remaining wall below the
deepest pocket feature is 4.6 mm.

**This set is not claimed print-ready.** The wall and overhang gates were
measured on every one of the 55 printable parts at a 0.4 mm nozzle during the
Make rounds and all 55 passed; those reports are under `cad/measure/`. The
integrated verifier was run without its print-gate tier, so the mesh gate was
never opened and no combined print-readiness verdict exists. Treat this as a
disclosed prototype.

## Limits of what has been checked

Everything here is digital. The CAD checks that ran do not establish printed
fit, tile retention, handling, real stack stability, durability or surface
finish, and no physical test has been run. Motion is unverified: this set has no
coupled mechanism and the operator's frozen Make option disables motion checks,
so no motion sweep was run and none is claimed. No dice-fairness claim is made
or possible, because the set ships no dice. Playtest was not run.
