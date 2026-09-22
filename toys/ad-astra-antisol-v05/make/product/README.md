# Antisol Hesper

Jungle Chess played with the solar system, in two armies of eight worlds.

A planet's size on the board is the fifth root of its real measured diameter,
so rank is something you can see rather than something you have to learn:
Mercury is the smallest world in play and Jupiter the largest. The traditional
rules are followed exactly as written. Matter faces antimatter -- one army's
worlds lean their poles one way and the other army's lean the other, by each
planet's own true axial tilt, and the bases say the same thing again in white
against black.

Four of the eight worlds wear the pattern a telescope shows, as circles and
bands. The other four wear a real map. Earth wears its own coastlines, Mars its
own dark continents, Mercury its own smooth plains with the Caloris basin in
them, and Venus -- alone in the set -- wears a surface no eye has ever seen.

Venus is the world this edition corrects. It used to wear its clouds. It now
wears the ground underneath them: the Magellan radar map, a golden amber ball
with the long sweep of Aphrodite Terra running most of the way round its
equator and three dark lowland plains around it. It is the only piece in the
set drawn from radar rather than from light, because Venus's surface is under
an opaque atmosphere and radar is the only way anyone has seen it. It is also
still upside down -- Venus's axis is tipped 177 degrees, so this is the one
world in the set whose map reads inverted, and that is the planet rather than a
mistake.

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

Four world pairs in this set have been corrected, one pair at a time, across
three runs plus the earlier Earth run. This is the last of them. A reader
picking the set up should be able to learn in one paragraph which worlds are
drawn from real outlines and which are drawn from atmosphere, without reading
four revision histories, so here is all eight in one line each:

- **Mercury** -- outline. Seven smooth albedo plains traced as rings, plus the
  Caloris basin as a bright floor inside a raised rim. *Corrected.*
- **Venus** -- outline. Seven radar highland provinces led by Aphrodite Terra,
  and three lowland plains, from the Magellan mosaic. *Corrected, this run.*
- **Earth** -- outline. Coastlines, dry interiors and a northern ice cap.
  *Corrected.*
- **Mars** -- outline plus cap. The classical albedo map, and two polar caps
  whose rims are broken by lobes so they read as ice rather than as lids.
  *Corrected.*
- **Jupiter** -- band plus blob. Six latitude belts and the Great Red Spot.
  *Reviewed and kept.*
- **Saturn** -- band. Four latitude belts, and the ring, which is geometry
  rather than a marking. *Reviewed and kept.*
- **Uranus** -- band. One faint belt, stood upright by the planet's own
  97-degree tilt. *Reviewed and kept.*
- **Neptune** -- blob plus band. The Great Dark Spot and three white cloud
  streaks. *Reviewed and kept.*

No world is bare.

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

**The verification finished this time, and that is worth saying plainly,
because it is the thing the last run could not say.** The pipeline ran for
1126 seconds and completed every check: 51 of 51 passed, none unverified, none
failed. All 24 printed parts cleared the mesh gate, the 45-degree overhang gate
and the 0.80 mm wall gate at a 0.4 mm nozzle; the 204-piece assembly validates
and nothing in it interferes with anything else. The previous run in this
correction chain stopped one check short — the wall-thickness check on Venus's
Sol world, its 83rd and last step, cut off when the geometry time allowance ran
out — and was handed over as an unverified prototype. That is the exact check
that passed here, at 0 of 160,826 wall samples below 0.80 mm. This is the last
correction of the four, so it is the run that gets to say it: **the whole set
is now verified, with nothing outstanding.**

Three checks were not run, and they are recorded as not run rather than as
passed: the mounting and power checks, because there is no bought part and no
powered system in this set to check, and the motion check, which is switched
off for this build — so **motion is unverified**, not passed. Nothing in the
set moves against anything else in any case.

**None of that makes this print-ready, and it is not claimed to be.** Every
number above is geometry. No part of this set has been printed, held, or
played with.

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
