# Mars's albedo atlas at globe scale

Mars's globe is Ø14.72 mm, so its radius is 7.360 mm and one degree
of arc is 0.1285 mm -- against Earth's 0.1457, because this is the
smaller ball.  The nozzle is 0.40 mm, which is the narrowest colour
boundary the printer can lay down and 3.11 degrees of arc here.

Measured on the sphere, in millimetres of arc, on the exact rings
`parts/mars_atlas.py` hands the build, by the arithmetic
`measure/atlas_resolution.py` already carried for Earth.

## Every ring

`half-angle` is how far the ring's furthest vertex sits from the
ring's own axis. The outline tool builds a radial prism through the
ring and refuses anything past 72 degrees.

| ring | vertices | perimeter mm | shortest edge mm | narrowest neck mm | half-angle deg |
|---|---|---|---|---|---|
| syrtis_major | 9 | 9.47 | 0.72 | 0.72 | 15.1 |
| mare_acidalium | 10 | 15.55 | 1.20 | 1.20 | 27.8 |
| sinus_sabaeus | 11 | 16.91 | 0.91 | 0.85 | 32.3 |
| sinus_meridiani | 6 | 4.55 | 0.64 | 0.64 | 7.3 |
| mare_erythraeum | 9 | 13.49 | 1.29 | 1.29 | 22.3 |
| mare_sirenum | 8 | 14.88 | 1.31 | 1.31 | 24.7 |
| mare_cimmerium | 9 | 17.98 | 1.74 | 1.67 | 32.3 |
| mare_tyrrhenum | 6 | 11.04 | 1.37 | 1.37 | 18.0 |
| cap_north_lobe_1 | 4 | 5.32 | 1.14 | 0.96 | 9.3 |
| cap_north_lobe_2 | 4 | 6.47 | 1.50 | 1.15 | 11.4 |
| cap_north_lobe_3 | 4 | 5.31 | 1.06 | 0.81 | 9.3 |
| cap_north_lobe_4 | 4 | 5.50 | 1.16 | 1.05 | 9.6 |
| cap_north_lobe_5 | 4 | 4.68 | 1.01 | 0.93 | 7.6 |
| cap_north_lobe_6 | 4 | 4.66 | 1.06 | 1.00 | 7.5 |
| cap_south_lobe_1 | 4 | 5.21 | 0.95 | 0.83 | 9.6 |
| cap_south_lobe_2 | 4 | 4.87 | 1.01 | 0.84 | 8.4 |
| cap_south_lobe_3 | 4 | 4.85 | 1.06 | 0.87 | 8.8 |
| cap_south_lobe_4 | 4 | 4.47 | 0.89 | 0.77 | 7.7 |

## The red between two dark regions

Two albedo rings running closer than the nozzle would print as one
region with a broken thread of red in it, which is worse than either
answer. Rings the atlas overlaps on purpose -- the three of the
southern belt -- are the next table instead.

| channel | width mm |
|---|---|
| mare_acidalium / sinus_sabaeus | 3.80 |
| mare_acidalium / sinus_meridiani | 2.55 |
| sinus_sabaeus / sinus_meridiani | 0.46 |
| sinus_sabaeus / mare_erythraeum | 0.97 |
| sinus_sabaeus / mare_tyrrhenum | 2.27 |
| sinus_meridiani / mare_erythraeum | 2.96 |
| mare_erythraeum / mare_tyrrhenum | 1.89 |

## The southern belt's own joins

Sirenum, Cimmerium and Tyrrhenum are meant to fuse into the one dark
belt the reference shows. Separate rings are only how that belt is
described, so what these two joins have to do is overlap -- an
approach, however close, leaves a thread of red the nozzle cannot
lay down.

| join | shared area mm2 | deepest bite mm |
|---|---|---|
| mare_cimmerium / mare_tyrrhenum | 0.23 | 0.53 |
| mare_sirenum / mare_cimmerium | 0.46 | 0.37 |

## The polar caps' broken rims

A blob centred on a pole is a polar cap, and the two blobs are
unchanged: 23 degrees of angular radius north, 21 south, which
puts their rims at latitude 67 and -69. What is corrected is that
both rims were exact circles of latitude, and a bare circular rim
reads as a lid laid on the globe rather than as ice.

Each lobe has to straddle its rim: vertices outside it, which is
what breaks the circle, and vertices inside it, which is what fuses
the lobe to the cap instead of leaving it floating off the edge.

| lobe | past the rim mm | inside the rim mm | to the next lobe mm |
|---|---|---|---|
| cap_north_lobe_1 | 0.51 | 0.77 | 1.17 |
| cap_north_lobe_2 | 0.77 | 0.64 | 0.75 |
| cap_north_lobe_3 | 0.39 | 0.77 | 0.95 |
| cap_north_lobe_4 | 0.64 | 0.64 | 0.75 |
| cap_north_lobe_5 | 0.51 | 0.77 | 0.62 |
| cap_north_lobe_6 | 0.77 | 0.64 | 0.63 |
| cap_south_lobe_1 | 0.39 | 0.64 | 1.80 |
| cap_south_lobe_2 | 0.51 | 0.64 | 2.03 |
| cap_south_lobe_3 | 0.39 | 0.64 | 1.92 |
| cap_south_lobe_4 | 0.39 | 0.64 | 2.19 |

The north cap carries 6 lobes against the south's 4 and reaches
0.77 mm past its rim at the deepest against 0.51 mm, so it is the
larger and the more irregular of the two, as the reference shows.

## The red a cap leaves against the albedo

`caps` is cut back by `albedo`, so where an albedo ring runs close
to a cap's rim or one of its lobes, the red strip between them is
that narrow. Nothing on this globe comes near: the northernmost
albedo ring is Acidalium and the southernmost is Erythraeum.

| cap | nearest albedo ring | red between mm |
|---|---|---|
| north | mare_acidalium | 0.77 |
| south | mare_erythraeum | 2.70 |

## What the atlas does not draw

Omissions this build made on purpose, each with its reason, so
nobody has to wonder whether it was an oversight.

- **craters** -- at this radius a crater reads as a print defect rather than as a crater, and the reference shows none.  This is the same judgement the markings table already records for Mercury.
- **Olympus Mons and the Tharsis volcanoes** -- relief rather than albedo, and flat in a distant view.  A raised cone would also be the one thing on this globe that breaks its outer sphere, which is what every marking here exists not to do.
- **Valles Marineris** -- drawn generously it is about 0.4 mm wide at this globe size, so it could not carry a colour boundary on both sides.
- **Hellas and the bright basins** -- a fourth filament, and Mars has exactly three here -- red, cocoa_brown and white.
- **the bright beige highlands** -- the same; the globe's own red IS the highlands on this piece.
- **the dark collars that ring the real caps in spring** -- not in the reference, and at this size a collar reads as a mistake in the cap rather than as seasonal ice.

## Simplifications

- **mare_cimmerium** -- western edge moved 3 degrees of longitude west, from (190, -18) and (196, -31) to (187, -18) and (193, -31), 0.37 mm; and the eastern vertex 5 degrees east, from (250, -22) to (255, -22), 0.60 mm.  The western move closes the Sirenum join above.  The eastern one closes the Tyrrhenum join, which as drawn left 0.34 mm of red between two rings the appendix means to fuse; with Tyrrhenum's south-western vertex moved to meet it the two overlap by 0.24 mm2 and bite 0.53 mm into one another.  The eastern vertex ends up inside Tyrrhenum and the western one inside Sirenum, so again the belt's outline is where it was drawn.
- **mare_sirenum** -- eastern edge moved 4 degrees of longitude east, from (188, -20) and (190, -30) to (192, -20) and (194, -30): 0.48 mm on this globe.  As drawn, Sirenum and Cimmerium came no closer than 0.32 mm, a thread of red narrower than the 0.40 mm nozzle, where the appendix means the two to fuse into one belt.  With Cimmerium's western edge moved to meet it the two now overlap by 0.46 mm2 and bite 0.37 mm into one another.  Both moved vertices end up inside the other ring, so the belt's own outline does not move.
- **mare_tyrrhenum** -- south-western vertex moved 5 degrees of longitude west, from (256, -29) to (251, -29), 0.56 mm, closing the Cimmerium join described above.  It moves into the notch between the two rings, which is the part of the belt the appendix asks to be filled.
- **sinus_meridiani** -- south-western vertex lifted 1 degree of latitude, from (354, -6) to (354, -5), 0.13 mm.  As drawn, Meridiani and Sabaeus came no closer than 0.36 mm and the red channel between them was under the nozzle.  These two are not a fused pair -- the appendix draws them as two features with sea between -- so the channel was opened to 0.46 mm rather than closed.  One degree is the smallest move that clears the nozzle, and neither outline changes shape.

- **sinus_sabaeus** -- carried vertex for vertex.  It is the thinnest feature on this globe and the one the Wish names as most at risk, so it was measured rather than assumed: its narrowest printable width is 0.85 mm, twice the 0.40 mm nozzle.  It was neither widened nor dropped, and it is not a blob.

## Verdict

Nothing in the atlas falls under the 0.40 mm nozzle at this
globe size: no ring edge, no neck, no red channel, no cap lobe
gap and no strip between a cap and the albedo. Both belt joins
overlap rather than approach. No feature was dropped, and the
one ring the Wish names as most at risk -- Sinus Sabaeus -- is
carried at the width it was drawn.

Measured by `measure/mars_atlas_resolution.py` on the exact rings in
`parts/mars_atlas.py`.
