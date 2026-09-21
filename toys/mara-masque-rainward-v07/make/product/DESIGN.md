# Rainward Sunflare - design handoff

Selected inventor `mara-masque`, bound by the host at the Workshop selection
boundary (`workshop_selection.status: selected`). This Manager runtime
materialises no `mara-masque` custom subagent, so the root Manager applied
Mara's exact Taste from `.codex/agents/mara-masque.toml` directly rather than
delegating the design; the independent blind review of the canonical images was
delegated to a separate native critic that had not seen the Wish. This document
is the completed design dependency the CAD consumes. It is not a passing
geometry or review claim.

Backgammon on a Sun. Two streams of condensed plasma travel 24 radial lanes,
scatter lone drops onto the exposed flare at the centre, and rain back out of
play. The rim is a crown of 32 separate licks of flame standing off the disc's
own circular edge.

## What this correction is

Rainward Emberfan is mechanically right, and the last correction fixed the rim
that mattered: the flames were made to stand apart, each rooted on its own arc
of an unbroken base circle with a valley of open ground between every pair. The
blind critic measured that rhythm - 48 roots averaging 50.2 px against 45 bare
stretches averaging 50 px - and withdrew its earlier reservation. **That is
carried here untouched. There is no return to a fused skirt.**

One thing still failed. Across two independent naive reads the same critic
never once reached for sun, flame or fire. It called the object a rosette, a
medallion, a pinwheel disc with an almost creaturely fringe, and said plainly:
*"The uniform one-way handedness reads as rotation, which actively competes
with the fire reading."* Forty-eight thin same-handed tendrils on a plate read
as a wheel.

This revision makes three changes, all to the corona, all aimed at that:

1. **Fewer flames, twice as wide at the root.** 48 becomes 32.
2. **A tongue, not a fin.** The taper profile is reversed and the tip cap
   halved.
3. **Mixed handedness.** Fourteen of the 32 curl the other way.

Nothing else moves: not the rules, not the parts list, not the 24 lanes and
their two tones, not the tile fan or the 0.70 mm orange margin, not the centre
bar or its bank ticks, not the counter, the stations or the stack, not the five
sealed colours or their greyscale ordering, and not the approved flame curve.

## Rule equivalence

`RULES.md` is carried over byte-identical, sha256
`d601a858b70b4c1685dced91c7f176d73e4779a3ad784e9b13c7fc88d1fd9d66`, confirmed
by hashing the copied file. Every frozen behaviour it states - player count,
component functions and quantities, setup, turn order, legal actions,
information, randomness and probabilities, state transitions, interaction,
ending, tie-breakers and scoring - is unchanged. Nothing in it was edited,
because the box is not the rules.

## The player-supplied allowance

Mara's Taste lets the human owner designate named standard commodity components
as player-supplied. The owner invoked it for the two dice and the two cups, and
this correction keeps that decision untouched. The ledger keeps the dice and
cups with unchanged function and quantity; the product summary and the README
state, before any other component detail, which components the player supplies
and the ordinary specification each must meet; and no printed randomiser,
spinner or substitute is added.

## Change 1 - fewer flames, twice as wide at the root

`CORONA_COUNT` is 32. `CORONA_ROOT_FRACTION_MAX`, `CORONA_ROOT_SPREAD`,
`CORONA_GAP_LO` and `CORONA_GAP_HI` are held exactly where they were, so the
one-to-one root-to-valley rhythm survives the count change by construction
rather than by search: both the root and the valley grow by the same half
again.

| | previous build | this build |
|---|---|---|
| flames | 48 | 32 |
| root-to-root pitch | 10.433 mm | 15.649 mm |
| root arc on the base circle | 5.104 to 5.622 mm | 7.665 to 8.424 mm, mean 8.047 |
| valley arc between two roots | 4.821 to 5.366 mm | 7.277 to 7.942 mm, mean 7.602 |
| widest root over its own root-to-root arc | 0.5246 | 0.5246 |
| valley over the smaller root beside it | up to 0.9941 | 0.9062 to 0.9895 |

Every flame's rise and the tall/mid/short banding are kept. The tall flames are
re-derived for 32: eight of them - one in four - at indices 0, 3, 8, 12, 15, 21,
25 and 28, spacing 3, 5, 4, 3, 6, 4, 3, 4. That set has four distinct spacings,
is never every fourth flame, and is neither periodic nor mirrored round the
ring; `validation.py` fails the build on any of those. Lengths span 4.150 to
17.000 mm, a ratio of **4.096 to one** - the previous build measured 3.65 and
fell short.

## Change 2 - a tongue, not a fin

The previous build's half width fell as `(1 - t) ** 1.50`, a curve that is
steepest at the root and flattest at the tip: it shed 65 per cent of the
surplus over the cap by mid length and then ran the outer third out at
essentially cap width. That is the near-parallel filament the Wish names.

The profile is turned round rather than merely re-exponented. The half width
now falls as `cap + surplus * (1 - t ** 1.50)`, which leaves the root flat and
arrives at the cap steeply. Three candidate exponents - 1.0, 1.5 and 2.2 - were
drawn as unwrapped silhouettes and compared against the concept strip before
1.5 was kept: 2.2 read as clubs, and 1.0 shed its width from the root.

| Wish target | measured |
|---|---|
| width at half length, at least 45 per cent of root width | **73.13 to 76.39 per cent**, mean 74.62 |
| tip cap across, 2.00 to 2.60 mm | **2.000 to 2.600 mm** |
| tip a quarter to a third of the base | 0.240 to 0.332 of the root chord |
| every tip blunt, nothing terminating in a point | every tip is a circular cap of radius 1.00 to 1.30 mm on a flame at least 3.312 mm tall in Z |

The flank now converges on the tip cap at about 30 degrees per side, against
about 2 degrees before. That is the number that stops it reading as a filament.

The earlier brief's *"treat 2.10 mm as the floor, not the target - if the critic
still reads needles at 2.10, go wider"* is withdrawn by this Wish. It was
one-sided and it drove the caps to 4.10 mm, which read as thumbs. The needle
test still has to pass, and does.

## Change 3 - mix the handedness

`CORONA_SENSE[i]` is +1 when flame i curls toward the neighbour it faces at the
end of its own root arc - the sense every flame had - and -1 for the exact
mirror of that flame about its own radial midline. The mirror keeps the root
chord, the root arc, the turn magnitude, the taper, the cap, the ramp and the
print pose, so no other measured value in this document moves because of it.

The printability argument for a single handedness is withdrawn, and it was
wrong. The corona lies flat in the print plane; a flame's curvature is entirely
in plan, in X and Y; the 45-degree rule governs Z only. Curving one flame one
way and the next the other costs nothing in overhang, support or bridging, and
the part remains a single flat plan piece.

| Wish clause | measured |
|---|---|
| at least one flame in three leans the opposite way | **14 of 32**, 0.4375 |
| roughly a third to a half turn the minority way | 0.4375, inside [1/3, 1/2] |
| runs of one to three | 2, 2, 1, 2, 1, 1, 1, 2, 1, 3, 1, 2, 2, 1, 2, 1, 2, 3, 1, 1 - shortest 1, longest 3 |
| never strictly alternating | false; there are runs of 2 and 3 |
| never a pattern that repeats round the ring | no rotation by 1..31 reproduces the sequence |
| two neighbours leaning toward each other hold 0.80 mm | 10 converging pairs; the narrowest gap between any two flames at all is **7.275 mm**, nine times the floor |
| flip one of a pair rather than shorten either | implemented as `CORONA_SENSE_FLIPS`; empty, because no pair came near the floor |
| turn magnitude and shape unchanged | exponent 1.15, 37.13 to 43.24 degrees root to tip, 0.4506 of the turn in the inner half |

The sign string, read round the ring from flame 0, is
`++--+--+-+--+---+--++-++-++---+-`.

### The walk constant was chosen for legibility, not only for the statistics

This is the one place where the first build of this revision failed its own
review, and it is worth recording exactly why.

A flame's visible rake is its tip's tangential offset from its own root
midpoint, and that offset scales with length: 5.1 to 6.1 mm on a tall flame
against 1.8 to 2.2 mm on a short one, on an 8.05 mm root. Only the eight tall
flames therefore carry the handedness at a glance. The first constant tried,
frac(sqrt(19)/2), produced a correct 14/18 split and passed every clause in the
table above - but those eight tall flames came out in same-sign pairs,
`+ + - - + + - -`: a clean period-4 sweep in exactly the flames the eye reads.
The independent critic, shown only the images, duly reported *"a consistent
counterclockwise sweep around the disc, like a pinwheel"*.

The repair moved only the walk constant, to frac(sqrt(117)/2). The generator,
the run caps, the minority share and the run-length bounds are unchanged. The
eight tall flames now differ from their tall neighbour at **six of eight**
steps, in the irregular order `+ - - + - - + -`. Walks that alternate all eight
were found and rejected: they collapse the whole ring to a near-strict zigzag,
which is the repeating pattern the Wish forbids from the other side.

## Deliberately not changed

The tile fan still ends at radius 79.55, leaving a 0.70 mm orange margin, so
the flames still rise almost directly off the tile ends rather than out of a
wide orange band as they do in the concept. The Wish puts that out of scope:
widening the band means pulling the tile ring inward, which would strand the
outermost counter station at radius 74.0. That is a board change, not a rim
change. The tile geometry is byte-for-byte the clone's.

## One defect found and repaired that the Wish did not ask for

The plan used to start flame 0's root exactly on the disc cylinder's own seam
at angle zero. Two vertices a femtometre apart then had to be merged there, and
the kernel resolved that tie differently from run to run: the exported
`part_sun_orange.step` alternated between two byte orderings whose only
difference was the last bit of six coordinates, at (79.7, ~0, 0) and
(79.7, ~0, 5.4). `_plan()` now begins the ring half the closing valley past
zero, so bare base circle covers the seam. Six consecutive generations then
hashed identically. It is a constant rotation of the whole corona: no root arc,
valley, rise, turn, cap, clearance or tip radius changes.

## Every carried-over number, measured on this build

| carried-over requirement | measured |
|---|---|
| disc radius | 79.70 mm |
| tile fan on one exact circular arc, all 24 tiles | 79.55 mm; bays, notches or scallops: 0 |
| constant orange margin | 0.70 mm at all 24 boundaries |
| base circle unbroken, a valley for every pair | roots and valleys close the circle to 1e-6; 0 adjacent roots touching |
| no bare stretch longer than a flame's own root | widest valley over the smaller root beside it 0.9895 |
| no closed loop, arch, ribbon or handle | 0 interior rings, 1 plan piece, 0 such callables |
| counter | 10.0 x 7.0 x 4.5 mm, 30 of them, one solid |
| stations, lane inner radius | 74.0, 63.5, 53.0, 42.5, 32.0; 26.5 mm |
| outermost counter fully supported | 1.0 of its footprint on its own tile; 0.0 mm2 on any neighbouring tile |
| tallest flame tip, tip-to-disc | 96.700 mm, 1.2133 against the concept's 1.22 |
| envelope at most 194 mm | 189.213 by 183.186 mm |
| flame length span at least 4 to 1 | 4.150 to 17.000 mm, **4.096** |
| tall flames a minority of about one in four, unevenly spaced | 8 of 32, spacing 3, 5, 4, 3, 6, 4, 3, 4 |
| tip at least 3.0 mm tall in Z, root height 5.4 | 3.312 to 4.202 mm; 5.400 mm |
| one clean plane per flame top, material off the top only | true; ramp slopes 6.71 to 17.14 degrees, no hold before the fall |
| stack | deck 5.4, tile top 6.0, bar top 6.2, tile 2.2 on 3.8 mm of body |
| three oranges, body between the lane tones | #FF671F body 0.5103, #FFB549 light 0.7410, #8E3C06 dark 0.2882 |
| greyscale separability | cream 0.9377 > light > body > dark > brown 0.1741; smallest gap 0.102 measured in the render |
| RULES.md byte for byte | sha256 `d601a858...1fd9d66`, confirmed |
| 55 parts, no dice, no dice cups | 1 Sun board, 24 lane tiles, 30 counters |
| one plan piece, nothing floating, no overhang over 45 degrees, zero support, zero bridges | wall and overhang gates pass on all 55 printable entries at a 0.4 mm nozzle and 45 degrees |
| assembled.step under 12 MB, Sun part under 6 MB | 6.44 MB and 4.23 MB |

The rim is also counted from pixels rather than from parameters:
`cad/measure/render_audit.py` masks the board in `cad/snap/top.png`, keeps only
what lies outside radius 79.70 + 0.45 mm and labels the connected regions. A
rim that was poured and set is one region. This one is **32**, one per flame.

## What is not claimed

No print of this set has been made. Nothing here claims physical handling, tile
retention in its pocket, stack stability, durability, comfort,
discoverability, or how anyone responds to it. Dice fairness is a property of
the dice the player supplies. Motion is unverified: the set has no coupled
mechanism and the operator's frozen Make option disables motion checks. Still
images cannot prove motion, and none is claimed.
