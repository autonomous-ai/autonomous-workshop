# Rainward Flarecrown - design handoff

Selected inventor `mara-masque`, bound by the host at the Workshop selection
boundary (`workshop_selection.status: selected`). This Manager runtime
materialises no `mara-masque` custom subagent, so the root Manager applied
Mara's exact Taste from `.codex/agents/mara-masque.toml` directly rather than
delegating the design; the independent blind review of the canonical images was
delegated to a separate native critic that had not seen the Wish. This document
is the completed design dependency the CAD consumes. It is not a passing
geometry or review claim.

Backgammon - coronal-rain theme: rival streams of condensed plasma travel
magnetic lanes, scatter lone drops, and rain back into a Sun whose whole rim is
one unbroken crown of flame.

## What this correction is

Rainward Corona is mechanically right and its rim is wrong. Nineteen tongues
and one loop sat on the perimeter in tight pairs and triples with bare arcs of
22 to 46 degrees between the groups. Each tongue was narrow at the root and
swept away tangentially, so from above it read as a thin detached crescent lying
beside the disc. Twenty such clippings around three quarters of an empty circle
did not read as a corona; they read as damage.

This revision changes exactly one thing: the rim. Everything else - the rules,
the parts list, the 24 lanes and their two tones, the centre bar, the lane
stations, the board plan inside radius 86, the five sealed colours and their
greyscale ordering, and the built heights of deck 8.0, tile top 8.8 and bar top
9.0 - is carried over unchanged from the set being corrected.

## Rule equivalence

`RULES.md` is carried over byte-identical, sha256
`d601a858b70b4c1685dced91c7f176d73e4779a3ad784e9b13c7fc88d1fd9d66`. Every
frozen behaviour it states - player count, component functions and quantities,
setup, turn order, legal actions, information, randomness and probabilities,
state transitions, interaction, ending, tie-breakers and scoring - is unchanged.
The rule-equivalence ledger inside it still lists one shared pair of ordinary
1-6 dice and two dice boxes with their unchanged function and quantity. Nothing
in it was edited to match the reduced box, because the box is not the rules.

## The player-supplied allowance

Mara's Taste, revised 2026-09-17, lets the human owner designate named standard
commodity components as player-supplied. The owner invoked it for the two dice
and the two cups, and this correction keeps that decision untouched. The
allowance is a packaging decision and never a rules decision. The ledger keeps
the dice and cups with unchanged function and quantity; the product's own
summary and README state, before any other component detail, which components
the player supplies and the ordinary specification each must meet; and no
printed randomiser, spinner, teetotum or card draw is substituted.

## The correction, clause by clause

Every number below is measured on the exact plan the CAD extrudes, by
`cad/measure/check_corona_plan.py`, and recorded in
`cad/measure/corona-skirt-audit.json`.

1. **Between 32 and 44 tongues.** 38.
2. **No plain circular edge.** Every point on the perimeter belongs to a tongue
   flank or a trough. The longest arc anywhere that still lies within half a
   millimetre of the old radius-90 circle is 1.198 degrees, against a limit of
   four.
3. **Broad roots that meet.** The narrowest root measures 8.409 mm and no
   root is below 1.156 of its own tongue's radial length, against a floor
   of 6 mm and 60 percent. Consecutive tongues share their root points exactly,
   so the measured join gap is 0.0 mm and the crown is one continuous band.
4. **Uneven lengths.** Radial length runs 2.325 to 9.085 mm, a ratio of
   3.908. No two tongues are the same length or the same width. The sequence
   is checked against every circular shift, every mirror axis and every
   monotone run in `validation.py`, so it is neither periodic, mirrored nor
   sorted.
5. **Real flame depth.** 8 troughs measure at least 9 mm from their floor
   to the tip of an adjacent tongue and the deepest measures 9.24 mm.
6. **Nothing floats.** The body's plan is a single closed boundary with one
   hole in it. Every tongue is the same solid as the deck, because the crown
   outline *is* the deck's outline: there is no disc underneath with separate
   pieces fused to it.
7. **One hero loop.** One arch spans 16 degrees of the rim, rises to radius
   99.0 - the one place the rim goes that far out - and encloses a single
   closed loop of 81.513 mm2. Its two legs plunge through trough floors into the
   body, and two tongues of the crown run on underneath it inside the loop, so
   it rises out of the skirt rather than replacing a stretch of it.

Every tongue leans the same way round the ring, and the lean is scaled to the
tongue's own span so a narrow tongue never swings its tip past its own root.
The whole boundary stays single-valued in angle, which is what guarantees the
outline is simple and star-shaped and lets the tiles be clipped against it
exactly.

## The three disclosed engineering decisions

All three are mine, not the operator's.

1. **A trough may cut inside radius 90 only at a lane boundary.** Depth is what
   the correction asks for and the 194 mm envelope caps tongue length, so the
   depth had to come from the trough side. A trough that cuts inside radius 90
   also notches the tile lip above it, and a notch under a counter would remove
   flat support. There is a free window about eight degrees wide centred on
   every lane boundary where no counter at the outermost 85 mm station has any
   footprint. Twenty-four troughs use those windows, each jittered off its
   boundary; fourteen more sit near a lane axis and stay outside radius 90. The
   measured worst own-tile support is 0.90769, and the same measurement on tiles
   with no notch at all reports 0.90763 - the notches cost the outermost
   counter nothing, and `check_corona_plan.py` measures both numbers and
   compares them every run.
2. **The pocket outer wall moves from 86.5 to 84.5.** The correction Wish
   explicitly reopened that radius. The deepest trough floor is at radius 87.00,
   which would have left half a millimetre of body over a pocket wall at 86.5.
   At 84.5 it leaves 2.50 mm. The tile lip grows from 3.5 to 5.5 mm and still
   rests on the ring for its whole length, so nothing is cantilevered, and the
   tile locating key moves from radius 81.5 to 78.5 to stay inside the shorter
   pocket. Its clearance to the nearest counter landing region is unchanged at
   2.05 mm.
3. **The crown is built as exact curves, not a dense polygon.** 38 tongues
   carry 152 exact Bezier and arc edges instead of some thousands of chords.
   Each flank meets the tip cap along the tip axis, so the tip is
   tangent-smooth, and the solid stays cheap enough to tessellate inside the
   print gates' time allowance - the gate that timed out on the sun body in the
   set being corrected.

## What did not change

The 24 lanes, their two alternating tones, the centre bar, the lane stations and
the whole board plan inside radius 86. The five sealed sRGB colours and their
greyscale ordering. Deck 8.0, tile top 8.8, bar top 9.0. The counter silhouettes
at 12 x 8 x 4 mm with their original Bezier control points. The parts list: one
Sun board, 24 lane tiles, 30 counters, 55 parts, no dice and no dice cups. And
`RULES.md`, byte for byte.

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
obscures a sightline across the board to any lane. The crown sits 0.8 mm below
the lane tops at the rim and cannot hide a counter. The centre bar clears the
lane tops by 0.2 mm and stays a broad open circle, so reaching into it is
unobstructed. The four boundary markers rise 0.2 mm above the lane tops and sit
between lanes, never in a landing region - the fit audit measures zero contact
between any counter footprint and any marker. Lane state is readable two ways at
once: by tone in the coloured set, and by geometry alone in a single-material
print. These are geometric checks; they are not observed human play, and this
route runs no Playtest.

## A note on proportion

The reference this rim is compared against has flames a fifth to a third of the
disc radius. That cannot be built here: a 90 mm disc with flames that long needs
a 210 to 230 mm envelope and will not fit the declared 200 mm bed, and the play
disc cannot shrink because five 12 mm counters stacked along a lane already need
about 60 mm of radial room. Length is capped at 9.085 mm. Density, continuity
and root width are not capped, and that is where the effort went.

## Sources

The frozen research and rules provenance carried over from the clone remain the
basis for the rule ledger; they are historical evidence, not newly verified web
claims. The coronal-rain subject rests on NASA's account of unexpected rain on
the Sun - plasma cooling, magnetic-loop descent and reconnection - which
supports the theme's imagery and none of the game's blocking, probability or
result mechanics. The closest named collisions recorded in the clone, a lunar
luxury backgammon set and a circular backgammon board, are unchanged: the circle
is not claimed as novel, and no file, dimension or artwork from either is used.

## Construction

`cad/rainward_spec.md` holds the exact geometry, the dimension ledger with a
provenance tag per value, and the list of checks that must actually be measured.
No construction decision is delegated to the operator.
