# Antisol Jove

Jungle Chess played with the solar system, in two armies of eight worlds.

A planet's size on the board is the fifth root of its real measured diameter,
so rank is something you can see rather than something you have to learn:
Mercury is the smallest world in play and Jupiter the largest. The traditional
rules are followed exactly as written. Matter faces antimatter -- one army's
worlds lean their poles one way and the other army's lean the other, by each
planet's own true axial tilt, and the bases say the same thing again in white
against black.

Four of the eight worlds wear a real map: Earth its own coastlines, Mars its
own dark continents, Mercury its own smooth plains with the Caloris basin in
them, and Venus -- alone in the set -- a surface no eye has ever seen. The
other four wear their weather.

Jupiter is the world this edition corrects, and it is the largest piece in the
box. It used to wear six identical brown bands, each exactly twelve degrees
wide and evenly spaced about the equator. Nothing in the sky is that regular,
and the regularity was the one thing telling you that you were holding a
manufactured object rather than a planet. It now wears Jupiter's real belt
system: six belts at the latitudes they actually occupy, five, seven, ten,
thirteen, seven and six degrees wide, so no two of them match and no two gaps
between them match either. Between and beyond them are five bright cream zones,
the third tone the old piece was missing -- it had an orange ball and brown
bands and nothing else, so the bright zones were just bare globe and the
alternating rhythm that makes Jupiter legible was gone. The two widest belts
have a slight wave along their edges instead of running as exact circles of
latitude. And the Great Red Spot is one clean oval half again wider than it is
tall, where it used to be three overlapping circles that read as a lozenge,
with a darker collar around it and the widest belt bending north to make room
for it, the way the reference shows.

A cocoa-brown asteroid belt crosses the middle of the field, a star stands at
each end with two flames bursting off the board edge, and the three cells
around each star are sunken corona wells where a captured world drops out of
the light and its rank counts for nothing. You win by walking one of your
worlds onto the rival star.

## What arrives

Forty-two printed parts: sixteen worlds, a board in four panels, twelve
asteroid-belt tiles, two stars, six corona cells and two storage trays. Nothing
is glued, screwed or assembled; the tiles and stars drop into their own pockets
and the panels butt together.

## Where the eight surfaces come from

Five world pairs in this set have now been corrected, one pair at a time,
across five runs. A reader picking the set up should be able to learn in one
paragraph where each world's surface comes from, without reading five revision
histories, so here is all eight in one line each:

- **Mercury** -- outline. Seven smooth albedo plains traced as rings, plus the
  Caloris basin as a bright floor inside a raised rim. *Corrected.*
- **Venus** -- outline. Seven radar highland provinces led by Aphrodite Terra,
  and three lowland plains, from the Magellan mosaic. *Corrected.*
- **Earth** -- outline. Coastlines, dry interiors and a northern ice cap.
  *Corrected.*
- **Mars** -- outline plus cap. The classical albedo map, and two polar caps
  whose rims are broken by lobes so they read as ice rather than as lids.
  *Corrected.*
- **Jupiter** -- belt system. Six belts at Jupiter's own unequal latitudes,
  five, seven, ten, thirteen, seven and six degrees wide; five bright cream
  zones alternating between and beyond them; and the Great Red Spot as one
  oval, thirteen degrees of arc by nine, with a darker collar and the widest
  belt bending north around it. The two widest belts carry a slight wave rather
  than running as exact circles. Drawn from `ref/jupiter-sol.png` and its
  Anti-Sol mirror. *Corrected, this run.*
- **Saturn** -- band. Four latitude belts, and the ring, which is geometry
  rather than a marking. *Reviewed and kept.*
- **Uranus** -- band. One faint belt, stood upright by the planet's own
  97-degree tilt. *Reviewed and kept.*
- **Neptune** -- blob plus band. The Great Dark Spot and three white cloud
  streaks. *Reviewed and kept.*

No world is bare.

Those four were reopened at the owner's request, and they are being corrected
one pair at a time in the order Jupiter, Saturn, Neptune, Uranus; this run is
the first of them.

**Jupiter, Saturn, Neptune and Uranus were reviewed against their references
and deliberately kept as they are.** Their bands, their spot and their streaks
are finished work, not an unfinished job: a band system and a storm in an
atmosphere really are a belt of latitude and a round patch, so for those four a
circle is the honest shape rather than a compromise. The four that changed are
the four with a surface that has really been mapped.

## Before you print

Read `product.json` for the full list of limitations. Nothing here has been
printed, handled or played. Every fit, wall thickness and overhang margin is a
measurement on the exact CAD solids and a prediction for a 0.4 mm nozzle at
0.2 mm layers.

**The verification finished, and every check that could run did.** The
pipeline ran for 859 seconds over 83 steps: 79 passed, three were not
applicable and are recorded as not run rather than as passed, and none was left
unverified or failed. All 24 printed parts cleared the mesh gate, the 45-degree
overhang gate and the 0.80 mm wall gate at a 0.4 mm nozzle -- across the whole
set, 5,072,902 wall samples with no part over a tenth of one per cent below the
wall, and zero regions anywhere needing support. The 216-piece assembly
validates and nothing in it interferes with anything else.

That took two attempts and the first one is worth recording. The suite shares
one time budget across its geometry checks, the default is ten minutes, and on
a set this size the assembly's own validate-and-interfere pass spent most of it
-- so the run came back UNVERIFIED with the print gates on the last five parts
never started. Nothing had stalled and nothing had failed; the budget was
simply too small for 216 occurrences and 24 printable parts. It was raised
deliberately and the suite was run again, and this is that run.

Three checks were not run, and they are recorded as not run rather than as
passed: the mounting and power checks, because there is no bought part and no
powered system in this set to check, and the motion check, which is switched
off for this build — so **motion is unverified**, not passed. Nothing in the
set moves against anything else in any case.

**None of that makes this print-ready, and it is not claimed to be.** Every
number above is geometry. No part of this set has been printed, held, or
played with.

Jupiter now takes four filaments -- `orange`, `cocoa_brown`, `beige` and `red`
-- where it took three, which ties it with Earth as the most expensive world in
the box. The fourth is the bright cream of the zones, and it is `beige`, which
the set already carried on Earth's dry interiors and Venus's highlands, so no
new spool is loaded. What it is worth is measured rather than assumed:
`cad/measure/jupiter-tone-separation.md` renders one Jupiter piece twice at one
camera with only the zones repainted between the two, so the pixels that move
are the zones and nothing else moves at all, and it reports the separation
against both the orange globe and the brown belts for all four candidate
filaments. `sunflower_yellow` measured narrowest of the four and is also
Venus's whole globe now, so it was refused on both counts.

Venus is one of the worlds that takes three filaments -- `sunflower_yellow`,
`beige` and `cocoa_brown` -- where it used to take two. The amber is the
closest thing the shop stocks to the colour the Magellan mosaic is always
published in, and it was preferred to a new spool because the set already
carried it on the Sol star. What the highlands cost is measured rather than
assumed: `beige` on that amber separates 20.2 of 255 greyscale levels in the
canonical renders, the thinnest marking separation in the set, and it reads
only because Aphrodite Terra is one continuous band 117 degrees of longitude
wide. `cad/measure/venus-tone-separation.md` is that measurement, and
`cad/measure/venus-saturn-separation.md` is the check that Venus and Saturn are
still told apart now that their globes are neighbours in hue.

Mercury is the other world that takes three -- grey, cocoa brown and white --
for the reason measured in `cad/measure/mercury-tone-separation.md`.

The CAD project under `cad/` carries its own README, the full specification in
`cad/antisol_spec.md`, and every measurement this build made under
`cad/measure/`.
