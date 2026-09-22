# Antisol Caloris

Jungle Chess played with the solar system, in two armies of eight worlds.

A planet's size on the board is the fifth root of its real measured diameter,
so rank is something you can see rather than something you have to learn:
Mercury is the smallest world in play and Jupiter the largest. The traditional
rules are followed exactly as written. Matter faces antimatter -- one army's
worlds lean their poles one way and the other army's lean the other, by each
planet's own true axial tilt, and the bases say the same thing again in white
against black.

Five of the eight worlds wear the pattern a telescope shows as circles and
bands. Earth wears its own coastlines, Mars its own dark continents, and
Mercury its own smooth plains, because those three are the worlds in the set
with a surface a telescope really maps. On Mars, Syrtis Major -- the wedge
every telescope owner has drawn since 1659 -- is a triangle here rather than a
dot, the southern seas run together into one dark belt, and both polar caps end
on a ragged edge rather than on a drawn circle. On Mercury, the plains are
lobed regions that run together rather than a scatter of dots, and the Caloris
basin sits on the face you photograph: a bright floor inside a raised rim, the
one impact scar on the planet big enough to survive at this size.

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

## Before you print

Read `product.json` for the full list of limitations, and `GEOMETRY-NOTES.md`
for what this build did not finish checking. The short version: nothing here has
been printed, handled or played, and the verification pipeline ran out of its
geometry time allowance on its last step. Every fit, wall thickness and overhang
margin below is a measurement on the exact CAD solids and a prediction for a
0.4 mm nozzle at 0.2 mm layers. All 24 parts cleared the mesh and overhang gates
and 23 of 24 cleared wall thickness; the wall-thickness check on one part, Venus's
Sol world, was cut off and has no verdict either way. The set is not print-ready
and is not claimed to be.

Mercury is the one world that takes three filaments -- grey, cocoa brown and
white. The reason is measured rather than assumed: on the smallest globe in the
set the old dark grey was 21.8 of 255 greyscale levels away from the globe it
sat on, which is invisible at the size the piece occupies in a photograph.
Cocoa brown is 45.5, and the basin's white floor is what makes it read as a
basin. `cad/measure/mercury-tone-separation.md` is that measurement.

The CAD project under `cad/` carries its own README, the full specification in
`cad/antisol_spec.md`, and every measurement this build made under
`cad/measure/`.

<!-- workshop-geometry-disclosure -->
# Geometry inspection limitations

Geometry inspection is incomplete. This prototype is unverified and is not print-ready; see GEOMETRY-NOTES.md.

The following checks did not finish. No passing verdict is inferred from their interruption.

- check_thickness:part_world_venus_sol.step.py: geometry analysis cancelled or its time allowance exhausted (completed measurements: 0).
