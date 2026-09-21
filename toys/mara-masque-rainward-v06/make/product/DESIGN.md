# Rainward Emberfan - design handoff

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
play. The rim is a crown of 48 separate licks of flame standing off the disc's
own circular edge.

## What this correction is

Rainward Emberlick is mechanically right and its rim is wrong in two ways.

It carries a hero arch: one closed loop leaving the skirt and rejoining it. All
four blind critics of the previous chain flagged it in every round - spike tips
passing through the ribbon with no boolean cleanup, a tooth interpenetrating the
arch, no pad or blend where the legs meet the body, both feet diving behind the
tile plane without merging. Three repair rounds never resolved it.

And every brief since the second correction demanded that adjacent flame roots
meet with zero gap, so the skirt was one unbroken band. That rule is what made
the rim read as poured: with no air between the roots the licks fused into a
single wavy mass instead of standing as separate tongues.

This revision deletes the arch outright and withdraws the zero-gap rule.
Nothing else moves: not the rules, not the parts list, not the 24 lanes and
their two tones, not the centre bar, the lane stations or any part of the board
plan inside the tile edge, not the five sealed colours or their greyscale
ordering, not the approved flame curve, and not the built heights of deck 5.4,
tile top 6.0 and bar top 6.2.

## Rule equivalence

`RULES.md` is carried over byte-identical, sha256
`d601a858b70b4c1685dced91c7f176d73e4779a3ad784e9b13c7fc88d1fd9d66`. Every
frozen behaviour it states - player count, component functions and quantities,
setup, turn order, legal actions, information, randomness and probabilities,
state transitions, interaction, ending, tie-breakers and scoring - is unchanged.
The rule-equivalence ledger inside it still lists one shared pair of ordinary
1-6 dice and two dice boxes with their unchanged function and quantity. Nothing
in it was edited, because the box is not the rules.

## The player-supplied allowance

Mara's Taste lets the human owner designate named standard commodity components
as player-supplied. The owner invoked it for the two dice and the two cups, and
this correction keeps that decision untouched. The allowance is a packaging
decision and never a rules decision. The ledger keeps the dice and cups with
unchanged function and quantity; the product's own summary and README state,
before any other component detail, which components the player supplies and the
ordinary specification each must meet; and no printed randomiser, spinner or
substitute is added.

## Change 1 - the hero arch is gone

There is no `hero` module, no `hero_profile`, no closed loop, no arch, no
ribbon and no handle anywhere in the plan or in the solid.
`cad/measure/plan_audit.py` fails the build if any callable whose name contains
hero, arch, loop, ribbon or handle exists on the plan surface, or if the body's
plan carries any interior ring at all.

Measured: `1_closed_loops` 0, `1_hero_callables` empty, `1_plan_pieces` 1.

Where the arch stood, the rhythm simply continues. The 48 flames come from one
rule applied to the whole ring, so no angular window is special and there is no
seam or gap at the old location. The blind critic, told nothing, searched for a
loop in both naive reads and found none: "No arch, handle, hoop, ribbon or
closed ring anywhere ... every prong is open-ended and none joins a neighbour or
curls back to the body."

## Change 2 - the flames stand apart

The deck is now one plain cylinder of radius 79.70, so the disc keeps its own
circular edge unbroken all the way round. Each flame closes its plan face on its
own arc of that circle, which puts the whole flame outside the edge and makes
the arc the only place the two meet. Between two flames the boundary is that
bare circle, 0.4 mm under the deck top where the rim ring carries the tile lips,
with open background above it.

Root arcs and valleys are generated together so both of the Wish's separation
clauses hold by construction rather than by search: a valley is 0.940 to 0.995
of the smaller of the two roots it separates, which bounds each root at 55 per
cent of its own root-to-root arc from the other side.

| clause | measured |
|---|---|
| root arc on the base circle | 5.104 to 5.622 mm |
| valley arc between two roots | 4.821 to 5.366 mm |
| widest valley over the smaller root beside it | 0.9941 |
| widest root over its own root-to-root arc | 0.5246 |
| narrowest air gap between two flames in plan | 4.821 mm |
| narrowest gap to a second neighbour | 14.879 mm |
| adjacent roots touching | none |
| separate pieces of body outside the edge circle, counted in the render | 48 |

The last row is measured from pixels rather than parameters.
`cad/measure/render_audit.py` masks the board in `cad/snap/top.png`, keeps only
what lies outside radius 80.15 mm, and labels the connected regions. A rim that
was poured and set is one region. This one is 48, one per flame.

The blind critic, again told nothing: "The projections are clearly separate from
one another, not fused into a continuous band, with open background visible
between every pair" and "The disc retains its own uninterrupted circular edge
line, which can be traced smoothly past every prong." Neither naive read used
poured, melted, run or wax. On the unrolled rim it said the row "most resembles
a row of breaking waves or commas, or the licks on a cartoon sun".

## Every carried-over number, measured

| carried-over requirement | measured |
|---|---|
| disc radius | 79.70 mm |
| tile fan on one exact circular arc, all 24 | 79.55 mm, bays or notches 0 |
| constant orange margin | 0.70 mm at all 24 boundaries |
| counter | 10.0 x 7.0 x 4.5 mm |
| counters, identical solids | 30, one solid |
| stations | 74.0, 63.5, 53.0, 42.5, 32.0 mm |
| lane inner radius | 26.5 mm |
| outermost counter support | 1.0 of the footprint |
| tallest flame tip, tip over disc | 96.70 mm, 1.2133 against the concept's 1.22 |
| envelope | 186.674 by 188.459 mm, under 194 |
| flame length span | 4.15 to 17.00 mm, ratio 4.096 |
| tall flames | 12 of 48, one in four, spaced 3, 5, 4, 3, 6, 4, 3, 5, 4, 3, 4, 4 |
| turn exponent | 1.15 |
| total turn root to tip | 37.13 to 43.78 degrees |
| share of the turn in the inner half | 0.4506 |
| all flames turn the same way | true |
| tip caps across the plan | 2.60 to 4.10 mm |
| tip height in Z | 3.243 to 4.202 mm |
| root height | 5.4 mm |
| one clean plane per flame top, material off the top only | true |
| stack | deck 5.4, tile top 6.0, bar top 6.2, tile 2.2 on 3.8 mm of body |
| greyscale order, cream to dark brown | 0.9377, 0.7410, 0.5103, 0.2882, 0.1741 |
| parts | 55: one Sun board, 24 lane tiles, 30 counters |
| `RULES.md` | byte-identical, hash confirmed |

## Root width and valley, flame by flame

`cad/measure/plan-audit.json`, key `2_flame_table`, carries one row per flame:
its root start angle, root arc, root chord, the valley after it, the valley over
its own root, the root over its root-to-root arc, its rise, tip radius, tip cap,
turn and tip height. Across the 48: every valley is between 0.906 and 0.994 of
the smaller root beside it, and every root is between 0.5015 and 0.5246 of its own
root-to-root arc.

## Four disclosed engineering decisions

**Forty-eight flames.** The Wish fixes no count. Forty-eight puts the mean
root-to-root arc at 10.43 mm, which is the largest count whose roots still clear
the margin rule while every valley stays under its own roots, and it is the
density the concept image reads at.

**The tip cap runs the other way from the length.** A 17 mm lick ending in the
widest 4.10 mm cap reads as an oar. The mapping is squared, so only the shortest
nubs carry the widest cap and the long licks spend most of their length near the
2.60 mm one. Every tip is still blunt and rounded off.

**The bank markers moved to the centre bar.** The constant 0.70 mm orange margin
the Wish fixes leaves no boundary wide enough to carry the clone's raised
capsule out among the lanes: a 0.70 mm fin standing proud of the deck would be a
wall under the checked minimum. A first attempt put four raised dashes on the
hub ring, and the blind critic read them as "small hook-shaped slivers and
notches ... unclosed or overshooting geometry". They are now cut, not raised,
and sit on the centre bar's own top face as four radial V grooves 2.0 mm across
and 0.7 mm deep. A 10 mm drop bridges a 2.0 mm groove, so the bar stays a flat
unobstructed landing, and no tick lies under any of the six bar sites.

**The clone is an earlier link than the build the Wish restates.** The sealed
clone carries a 90 mm disc, 38 fused tongues, an 8.0 mm deck and 12 x 8 x 4 mm
counters. The Wish restates the last build as a 79.70 mm disc, a 5.4 mm deck and
10 x 7 x 4.5 mm counters, and its restated values govern. The clone supplies the
construction, the modules, the plan mathematics, the rule ledger, the counter
outline and the audit method, all reused here.

## What the innermost counter does, reported not hidden

The lane narrows toward the hub, so a 7.0 mm counter centred at the innermost
32.0 mm station reaches 0.3436 mm past its own tile's side edge. That reach
lands in the 1.00 mm orange margin between two tiles and never touches a
neighbouring tile: measured area on any neighbouring tile is 0.0 mm2. Support is
1.0 of the footprint at all four outer stations and 0.97974 at the innermost.
The Wish's own clause is about a counter at the outermost station, which is
fully supported.

## Printability, and what is not claimed

The wall gate at a 0.4 mm nozzle and the overhang gate at 45 degrees pass on all
55 printable entries; the 110 reports are in `cad/measure/`. Every part prints
flat-bottomed - the Sun underside down with material removed from every flame
top only, each tile top-face-down so its locating key points up, each counter on
its flat underside - and no part needs support or bridges.

Print readiness is not claimed. No print was made. No physical handling, tile
retention, stack stability, durability, human response or dice fairness is
claimed. Motion is unverified: the set has no coupled mechanism and the
operator's frozen Make option disables motion checks for this run.
