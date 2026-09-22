# Mercury's albedo atlas at globe scale

Mercury's globe is Ø13.78 mm, the smallest in the set, so its radius
is 6.890 mm and one degree of arc is 0.1203 mm.  The nozzle is 0.40 mm,
which is the narrowest colour boundary the printer can lay down and
3.33 degrees of arc here -- against 2.74 degrees on Earth and 2.63 on
Mars, the other two worlds drawn from outlines.

## Every ring

The vertex count is not fixed. `parts/mercury_atlas.vertex_count`
takes the most vertices a ring can carry with every edge still at or
above 0.50 mm, measured against that ring's own least radius, so a
strongly lobed plain gets fewer and larger steps and a nearly round
one gets more. This table is where that rule is checked rather than
trusted.

| ring | vertices | perimeter mm | shortest edge mm | narrowest neck mm |
|---|---|---|---|---|
| caloris_floor | 13 | 7.91 | 0.56 | 0.56 |
| caloris_rim | 23 | 13.49 | 0.52 | 0.52 |
| plain_equatorial | 19 | 15.24 | 0.55 | 0.55 |
| plain_far_side | 15 | 13.76 | 0.66 | 0.66 |
| plain_high_north | 20 | 15.95 | 0.55 | 0.55 |
| plain_north_west | 21 | 16.79 | 0.55 | 0.55 |
| plain_south_lead | 16 | 15.34 | 0.61 | 0.61 |
| plain_south_mid | 14 | 12.29 | 0.55 | 0.55 |
| plain_trailing | 12 | 10.75 | 0.67 | 0.67 |

## The gray between two plains

Unlike Earth's coastlines and Mars's maria, several of these are
*meant* to run together: the reference shows the smooth plains fusing
into larger regions rather than sitting apart as separate discs. A
pair whose boundaries cross is therefore the intended answer and is
listed as fused. Only a pair that comes close without crossing can
leave a channel of bare gray too thin to print.

| pair | gap | reads as |
|---|---|---|
| plain_north_west / plain_equatorial | -13.29 deg | fused, overlapping by 1.60 mm |
| plain_south_lead / plain_south_mid | -16.16 deg | fused, overlapping by 1.94 mm |
| plain_south_lead / plain_trailing | +5.74 deg | 0.69 mm of gray between them |
| plain_south_mid / plain_trailing | -10.21 deg | fused, overlapping by 1.23 mm |

Every pair not listed is more than 1.44 mm apart.

## The Caloris rim annulus

The rim is what is left when the floor's radial cone is subtracted
out of the outer ring, so its width is the difference between two
scalloped outlines and is the narrowest deliberate feature on this
piece. Both outlines are irregular on purpose -- a true circle at
this size reads as a drilled hole -- so the width is swept rather
than assumed.

| measure | degrees | mm |
|---|---|---|
| narrowest | 5.32 | 0.640 |
| mean | 7.50 | 0.902 |
| widest | 10.10 | 1.214 |
| the basin across, outer mean | 36.00 | 4.329 |
| the floor across, mean | 21.00 | 2.525 |

Caloris is about 1550 km across on a planet 4879 km in diameter,
which is 36 degrees of arc and 4.33 mm here, the number the outer
ring is drawn to.

## The gray between a plain and the seat

The globe is sunk into its disc and carried by a seat cone that
springs at latitude -42, so everything south of that parallel is
buried inside the collar and invisible. A plain whose southern
boundary lands in the 3.33 degrees just north of it would leave a
strip of bare gray under the nozzle, so every ring is held clear.

| ring | southernmost boundary | clear of the seat by |
|---|---|---|
| plain_north_west | -7.21 deg | 34.79 deg = 4.18 mm |
| plain_equatorial | -11.18 deg | 30.82 deg = 3.71 mm |
| plain_south_lead | -37.57 deg | 4.43 deg = 0.53 mm |
| plain_south_mid | -24.68 deg | 17.32 deg = 2.08 mm |
| plain_high_north | +13.48 deg | 55.48 deg = 6.67 mm |
| plain_far_side | -22.68 deg | 19.32 deg = 2.32 mm |
| plain_trailing | -13.63 deg | 28.37 deg = 3.41 mm |

## What the atlas does not draw

- **Craters.** Mercury is the smallest globe in the set at Ø13.78 mm, so one degree of arc is 0.120 mm and a 0.4 mm nozzle is 3.33 degrees of it. The reference shows craters everywhere, and the largest of them outside Caloris subtend three to six degrees -- one or two nozzle widths, with no room for a rim and a floor inside that. A crater drawn at this radius prints as a pit the width of a single extrusion and reads as a print defect rather than as a crater, and the set's material rules forbid deliberate grit. Caloris is the exception and is included precisely because it is the one impact feature large enough to survive: at 36 degrees of arc it is eleven nozzle widths across.

## Simplifications

- **plain_south_lead** -- mean angular radius 20.0 rather than the 22.0 the round patch used, and the strongest harmonic-one bias of the seven at 0.24 pointing north.  Drawn at 22 and evenly, its southern boundary reached latitude -44, which is past the -42 parallel where the seat cone springs and the visible sphere ends: the plain would have run out of globe, and anywhere it stopped just short would have left a strip of bare gray under the 0.4 mm nozzle.  Pulled north, the boundary stands at -37.6 and leaves 4.4 degrees, 0.53 mm, of visible gray between the plain and the seat.  The centre did not move.

## Verdict

Nothing in Mercury's atlas falls under the 0.40 mm nozzle at this
globe size: no ring edge, no neck, no gray channel between two
plains, no part of the Caloris rim annulus, and no strip between a
plain and the seat the globe stands on. The seven plains keep the
seven centres the round-patch build used.

Measured by `measure/mercury_atlas_resolution.py` on the exact rings
in `parts/mercury_atlas.py`.
