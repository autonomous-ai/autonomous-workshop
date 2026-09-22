# Antisol Kronos

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

Saturn is the world this edition corrects, and it is the only correction in the
chain that takes something away. It used to wear four identical brown bands,
each exactly twelve degrees wide and evenly spaced about the equator, in the
highest-contrast pair of colours in the whole box -- a dark cocoa brown on a
gold ball. Saturn does not look like that. Its own reference photograph is the
softest picture in the set: a cream-to-tan globe whose bands are wide and
soft-edged, whose strongest band is only a little darker than its neighbours,
and whose northern half is paler than its southern. Next to Jupiter, which is
loud on purpose and stands on the same board, Saturn is the quiet one, and that
contrast between the two pieces is worth having.

So the bands came down in tone rather than up. Four of them are now a mid amber
instead of a dark brown, and only the widest -- the one the photograph actually
lets you notice -- is still brown. There are five of them instead of four, at
nine, fifteen, eight, sixteen and twelve degrees wide, at five different
spacings, with no pair a mirror of another, because nothing in the sky is
regular and regularity is the one thing that tells you you are holding a
manufactured object. The two widest have a slight wave along their edges
instead of running as exact circles of latitude. And above fifty-eight degrees
north there is a bright cap in the same white as the ring, because the
reference brightens toward the north pole and the ring and the northern globe
are the same cream in it.

**Saturn's ring is untouched.** It is the one thing on this piece that already
worked, it is what the whole set's size ladder was solved against, and not a
number in it moved.

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

Six world pairs in this set have now been corrected, one pair at a time,
across six runs. A reader picking the set up should be able to learn in one
paragraph where each world's surface comes from, without reading six revision
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
  Anti-Sol mirror. *Corrected.*
- **Saturn** -- band system plus cap. Five bands at nine, fifteen, eight,
  sixteen and twelve degrees wide, unevenly spaced and not symmetric about the
  equator; four of them a mid amber and only the widest still brown, because
  this is the one world in the set whose reference is softer than the build
  was; the two widest carrying a slight wave rather than running as exact
  circles; and a bright cap above fifty-eight degrees north, in the white the
  ring already uses, because the reference brightens toward that pole. Drawn
  from `ref/saturn-sol.png` and its Anti-Sol mirror. The ring itself is
  geometry rather than a marking and is unchanged. *Corrected, this run.*
- **Uranus** -- band. One faint belt, stood upright by the planet's own
  97-degree tilt. *Reviewed and kept.*
- **Neptune** -- blob plus band. The Great Dark Spot and three white cloud
  streaks. *Reviewed and kept.*

No world is bare.

Those four were reopened at the owner's request, and they are being corrected
one pair at a time in the order Jupiter, Saturn, Neptune, Uranus; this run is
the second of them.

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

**The verification finished, and every check that could run did.** The pipeline
ran for 1,157 seconds over 83 steps: 79 passed, three were not applicable and
are recorded as not run rather than as passed, and none was left unverified or
failed. All 24 printed parts cleared the mesh gate, the 45-degree overhang gate
and the 0.80 mm wall gate at a 0.4 mm nozzle -- across the whole set, 5,072,902
wall samples with no part over a tenth of one per cent below the wall, and zero
regions anywhere needing support. The 220-occurrence assembly validates and
nothing in it interferes with anything else.

It took one attempt. The previous revision needed two, because the suite shares
one time budget across its geometry checks and the ten-minute default is too
small for a set this size; here that budget was raised deliberately before the
run rather than after a failure. Of the 1,157 seconds, 268 went on regenerating
every STEP from source and 536 on the single inspect batch that validates the
whole assembly, checks it for interference and validates all 24 printed parts.

Three checks were not run, and they are recorded as not run rather than as
passed: the mounting and power checks, because there is no bought part and no
powered system in this set to check, and the motion check, which is switched
off for this build -- so **motion is unverified**, not passed. Nothing in the
set moves against anything else in any case.

**None of that makes this print-ready, and it is not claimed to be.** Every
number above is geometry. No part of this set has been printed, held, or
played with.

Saturn now takes four filaments -- `yellow`, `sunflower_yellow`, `cocoa_brown`
and `white` -- where it took three, and it is the only world in the box whose
correction lowered its contrast rather than raising it. What the new band tone
is worth is measured rather than assumed:
`cad/measure/saturn-tone-separation.md` renders one Saturn piece twice at one
camera with only the bands repainted between the two, so the pixels that move
are the bands and nothing else moves at all. The amber separates **9.4** of 255
greyscale levels from the gold globe, which is the smallest separation this
project has ever committed to and smaller than the 21.8 it once rejected on
Mercury as invisible. That number is given rather than buried, because it is
the point: this world is supposed to be quiet. It reads because the bands are
enormous -- about 102,000 pixels of a 900-pixel frame, where Mercury's patches
were a few millimetres across -- and because an amber against a gold carries a
change of hue that a greyscale number does not count. The fallback tone the
brief allowed, `beige`, measured 10.1, seven tenths of a level better, and was
not taken.

One thing that costs, stated plainly. Saturn's band amber is the same
`sunflower_yellow` that is Venus's entire globe, so from this run the two
pieces are built out of the same spools.
`cad/measure/venus-saturn-separation.md` puts them side by side at the
product's own frame afterwards and answers on three counts separately: **size
and silhouette tell them apart easily** -- Saturn's globe is 9.47 mm larger, it
stands a third taller in the picture, and it wears a ring Venus has nothing
like -- and **the surface does not**. The surface is the weakest of the three
cues and this correction made it weaker. What still separates them there is
which way round the colours sit: Venus is a flat amber ball with one pale
province on it, Saturn is a lighter gold ball wearing the amber as soft stripes
with a white cap over its north.

Jupiter takes four filaments -- `orange`, `cocoa_brown`, `beige` and `red` --
for the reason measured in `cad/measure/jupiter-tone-separation.md`. Venus takes
three -- `sunflower_yellow`, `beige` and `cocoa_brown` -- where it used to take
two, and `beige` on that amber separates 20.2 greyscale levels, which was the
thinnest in the set until this run. Mercury is the other world that takes three
-- grey, cocoa brown and white -- for the reason measured in
`cad/measure/mercury-tone-separation.md`.

**What this correction could not do.** A flush colour inlay has a hard edge and
there is no way to make it soft. The reference's bands fade into one another;
these cannot, and every boundary on this globe is a colour change at a line.
Lowering the contrast is the substitute for softening the edge, not a cure for
it. Nothing else the planet shows was added: no hexagonal polar vortex, no
storms, no spokes in the ring, no ring divisions and no shadow of the ring on
the globe. Each was considered and each was rejected on arithmetic --
`cad/measure/saturn-atlas-resolution.md` carries it, the hexagon included,
whose visible edge is a quarter of one nozzle width.

The CAD project under `cad/` carries its own README, the full specification in
`cad/antisol_spec.md`, and every measurement this build made under
`cad/measure/`.
