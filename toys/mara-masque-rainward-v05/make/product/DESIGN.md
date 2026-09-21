# Rainward Bladefire - design handoff

Selected inventor `mara-masque`, bound by the host at the Workshop selection
boundary (`workshop_selection.status: selected`). This Manager runtime
materialises no `mara-masque` custom subagent, so the root Manager applied
Mara's exact Taste from `.codex/agents/mara-masque.toml` directly rather than
delegating the design; the independent blind review of the canonical images was
delegated to a separate native critic that had not seen the Wish. This document
is the completed design dependency the CAD consumes. It is not a passing
geometry or review claim.

Backgammon - coronal-rain theme: rival streams of condensed plasma travel
magnetic lanes, scatter lone drops, and rain back into a Sun whose rim is a
crown of curled flame laid back off the disc.

## What this correction is

Rainward Flarecrown is mechanically right and its rim is wrong in two ways.

Each tongue was a broad flat triangle extruded at the full 8 mm deck height,
with a vertical wall all the way round and only a small hooked nub at the apex.
At any angle other than straight down it was a solid block, so the rim read as
a cog, or the crimped edge of a bottle cap, rather than as fire coming off a
sun.

And the board had stopped reading as one object. An earlier correction asked
for an orange flame root reaching inward past the tile ends; the only way to
get it was to cut bays into the tile ends and to clip every tile back into the
troughs. The fan of 24 tiles no longer finished on a circle, every tile looked
bitten, and the sun looked torn.

This revision changes the shape of the tongues and puts the tiles back on their
circle. Nothing else moves: not the rules, not the parts list, not the 24 lanes
and their two tones, not the centre bar, the lane stations or any part of the
board plan inside the tile edge, not the five sealed colours or their greyscale
ordering, and not the built heights of deck 8.0, tile top 8.8 and bar top 9.0.
The 38 troughs and the 38 tip radii are carried over as the same table the
clone used, so tongue count, root widths, root joins, length spread and flame
depth are arithmetically identical to the set being corrected.

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
ordinary specification each must meet; and no printed randomiser, spinner,
teetotum or card draw is substituted.

## The correction, clause by clause

Every number below is measured on the exact plan the CAD extrudes and the exact
plane each tongue top is cut by, by `cad/measure/check_corona_plan.py`, and
recorded in `cad/measure/corona-skirt-audit.json`.

1. **Taper early.** A tongue is no longer a triangle stretched between its two
   root points. It is a swept blade: a spine with a width profile on it. The
   half width over the tip falls as the square-ish power `(1 - t) ** 4.2`, so
   the width comes off at once where the tongue leaves its trough - which is
   what makes the notch between two tongues a V rather than a scallop - and by
   mid length the blade is down to **0.268 of its own root at worst**. The root
   itself is untouched: it is still the full chord the tongue shares with both
   neighbours, **8.409 mm at the narrowest** and never below **1.156** of that
   tongue's own radial length.

2. **Turn through the outer half.** The spine leaves the root chord along that
   chord's outward normal and turns steadily one way. The heading follows
   `turn * t ** 2.4`, so four fifths of the turn happens beyond mid length
   rather than the tongue leaning over as a whole. Measured on the built spine:
   the tip tangent differs from the root tangent by **37.41 to 43.22 degrees**
   on every tongue, of which **29.91 to 34.56 degrees** happens inside the outer
   half alone. Every tongue turns the same way round the ring.

3. **Bring the top down.** Each tongue is built as its own flat-bottomed solid
   and fused onto the root chord it shares with the deck core. One plane per
   tongue then takes the top down. Root height stays **8.0 mm**, flush with the
   deck. Tip heights run **3.579 to 4.238 mm** and no two tongues share one -
   38 distinct values, dealt out against how far each tongue actually reaches,
   longest lowest, so the crown lies back at one attitude instead of a few stubs
   dropping off a cliff. The ramps fall at **24.9 to 58.5 degrees**.

4. **A clean ramp, not a slump.** The top is a single plane. It meets each
   vertical flank along one straight line, so both flank edges stay crisp the
   whole way out and nothing is blended or rounded over into a soft lump.
   Material comes off the top only: the underside of every tongue is flat on
   the bed, nothing is cantilevered over air, and the overhang gate reports zero
   regions needing support and zero bridges on every one of the 55 parts.

5. **Thinned, not sharpened.** The thinnest tip measures **1.50 mm across in
   plan**, against a floor of 1.3, and the lowest tip stands **3.579 mm** in Z,
   against a floor of 3.0. There is no needle and no spike anywhere on the rim.

6. **The tiles are put back on one circle.** Every tile's outer edge is one
   exact circular arc of radius **89.85** centred on the board - the same arc on
   all 24 - so the fan closes on a single continuous circle. The bays and the
   trough clipping are withdrawn entirely: zero notches, zero scallops, zero
   bays, no tile shortened, no radius changed, no tile plan altered in any other
   way. No orange flame root is visible inside the disc; the flame lives
   entirely outside that arc, where it already did.

7. **Everything the clone measured still holds.** 38 tongues; adjacent roots
   meeting with a measured join gap of **0.0 mm**; radial length **2.325 to
   9.085 mm**, ratio **3.908**; **8 troughs at or over 9 mm** of flame depth,
   the deepest **9.24 mm**; **one plan piece** with **one closed loop**, the
   hero arch, with the skirt running on underneath it; envelope **191.105 x
   192.514 mm**; outermost counter support **0.90769**.

## The four disclosed engineering decisions

All four are mine, not the operator's.

1. **The plain-circular-edge proxy moved from 1.198 to 1.317 degrees.** That
   number counts the longest angular run of perimeter lying within half a
   millimetre of the old radius-90 circle, measured by the clone's own method at
   the clone's own sampling density. It rose because a curling flank now sweeps
   across that radius instead of crossing it head on - not because a circular
   edge came back. `check_corona_plan.py` therefore also measures the run that
   is inside that band *and* within 15 degrees of tangential, which is what a
   plain circular edge actually is: **0.088 degrees**. There is no bare arc
   anywhere on the rim. The contract limit is 4 degrees and both numbers are
   well inside it. This is the one measured property from the correction brief
   that moved, and it moved as a side effect of the curl the brief asked for.

2. **A tile lip laps up to 2.75 mm past the body ring at the deepest troughs.**
   Every tile now ends on the same circle, so where a trough floor cuts inside
   radius 89.85 the outer corner of that tile's 1.0 mm lip reaches over the
   notch. It is a corner tab a few millimetres across on a part that prints flat
   and alone, so it costs no printed overhang and no support. It is reported
   rather than fixed by cutting the tile, because cutting the tile is exactly
   what this correction forbids. Every deep trough still sits in the free window
   at a lane boundary where no counter at the outermost 85 mm station has any
   footprint, so no counter loses support: that measures **0.90769**, the figure
   the brief requires it to hold.

3. **The fall starts at the root chord, and a rim collar carries the tile lips.**
   The first repaired build held the deck height out to radius 90 and only then
   fell, which left a short steep bevel sitting on a full-height wall. The
   independent critic, reading it blind, called that rim a crimped
   bottle-cap-meets-gear-tooth crown - the exact fault this correction exists to
   remove. Starting the fall at the root chord makes the ramp the face the eye
   sees, but on its own it would drop the body top under the outer millimetres of
   every tile lip. `rim_collar()` puts the body back up to the ring top across the
   band the lips occupy, clipped to the skirt plan so no trough is filled in,
   which keeps every lip carried and the flame laid back at the same time.

4. **The crown and the tiles are built from exact curves.** Each flank is a short
   chain of cubic Beziers fitted to the analytic blade to within **0.048 mm**,
   each tip cap is one arc, and each tile is two lines and two exact arcs instead
   of forty chords. That took the Sun part from 11.7 MB to **6.9 MB** and the
   assembled export from 48.3 MB to **9.2 MB**. The Sun part misses the brief's
   4 MB target; the remaining bulk is the hero arch's 280-sample plan, which is
   preserved geometry this correction is not allowed to touch. The sealed archive
   is far inside its 128 MiB limit either way.

## What did not change

The 24 lanes, their two alternating tones, the centre bar, the lane stations,
the capsule markers and the whole board plan inside the tile edge. The tile
plan, radius, lapping lip and clearances. The 38 troughs and 38 tip radii. The
hero arch. The five sealed sRGB colours and their greyscale ordering. Deck 8.0,
tile top 8.8, bar top 9.0. The counter silhouettes at 12 x 8 x 4 mm with their
original Bezier control points. The parts list: one Sun board, 24 lane tiles, 30
counters, 55 parts, no dice and no dice cups. And `RULES.md`, byte for byte.

## Recognition and the seated player

| Source-game element | Retained cue | Original astronomical expression |
|---|---|---|
| 24 points in four tables of six | 24 radial lanes, four countable banks | plasma lanes across the solar disc |
| Alternating point colours | 24 separate tiles in two tones | lanes lit and shadowed by the turning Sun |
| The bar | one low central circle | the exposed flare a hit drop is thrown onto |
| Two opposing sets of 15 checkers | two counter silhouettes and two colours | condensed plasma drops, one stream each |
| Board edge decoration | the flame crown | a corona of prominences and one closed magnetic loop |

Seated-position checks made on the exact geometry rather than on prose: nothing
on the board rises above 9.0 mm and the lane tops are at 8.8, so no feature
obscures a sightline across the board to any lane. The crown starts 0.8 mm below
the lane tops at the rim and falls away from there, so it cannot hide a counter.
The centre bar clears the lane tops by 0.2 mm and stays a broad open circle, so
reaching into it is unobstructed. The four boundary markers rise 0.2 mm above the
lane tops and sit between lanes, never in a landing region - the fit audit
measures zero contact between any counter footprint and any marker. Lane state is
readable two ways at once: by tone in the coloured set, and by geometry alone in
a single-material print. These are geometric checks; they are not observed human
play, and this route runs no Playtest.

## A note on proportion

The image this rim is chasing was generated, not engineered: its flames are long,
slender and sharply curled, which on a printer means spikes and sub-3 mm
features, and a 90 mm disc with flames that long needs a 210 to 230 mm envelope
and will not fit the declared 200 mm bed. Length is capped at 9.085 mm and that
is settled. What was available this round was the taper, the curl and the falling
top, and that is where the whole effort went.

## Sources

The frozen research and rules provenance carried over from the clone remain the
basis for the rule ledger; they are historical evidence, not newly verified web
claims. The coronal-rain subject rests on NASA's account of unexpected rain on
the Sun - plasma cooling, magnetic-loop descent and reconnection - which supports
the theme's imagery and none of the game's blocking, probability or result
mechanics. The closest named collisions recorded in the clone, a lunar luxury
backgammon set and a circular backgammon board, are unchanged: the circle is not
claimed as novel, and no file, dimension or artwork from either is used.

## Construction

`cad/rainward_spec.md` holds the exact geometry, the dimension ledger with a
provenance tag per value, and the list of checks that must actually be measured.
No construction decision is delegated to the operator.
