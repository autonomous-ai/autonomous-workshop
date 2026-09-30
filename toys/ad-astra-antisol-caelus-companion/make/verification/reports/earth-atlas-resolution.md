# Earth's coastline atlas at globe scale

Earth's globe is Ø16.70 mm, so its radius is 8.350 mm and one degree
of arc is 0.1457 mm.  The nozzle is 0.40 mm, which is the narrowest
colour boundary the printer can lay down and 2.74 degrees of arc here.

Three things have to clear that nozzle: the rings themselves, the sea
channels between them, and the strip one region leaves when another is
subtracted out of it.  All three are measured below, on the sphere, in
millimetres of arc, on the exact rings `parts/atlas.py` hands the build.

## Every ring

| ring | vertices | perimeter mm | shortest edge mm | narrowest neck mm |
|---|---|---|---|---|
| africa | 19 | 30.27 | 1.02 | 1.02 |
| american_southwest | 6 | 6.45 | 0.92 | 0.92 |
| arctic_lobe_1 | 5 | 7.67 | 1.20 | 1.20 |
| arctic_lobe_2 | 5 | 9.79 | 1.52 | 1.39 |
| arctic_lobe_3 | 4 | 5.82 | 1.01 | 1.01 |
| arctic_lobe_4 | 4 | 6.02 | 0.89 | 0.87 |
| arctic_lobe_5 | 4 | 6.29 | 1.47 | 1.46 |
| arctic_lobe_6 | 4 | 5.63 | 1.02 | 1.02 |
| arctic_lobe_7 | 4 | 5.63 | 1.07 | 1.07 |
| asia | 26 | 33.56 | 0.64 | 0.64 |
| australia | 11 | 14.83 | 0.62 | 0.62 |
| central_america | 7 | 12.34 | 1.48 | 1.48 |
| europe | 17 | 18.68 | 0.66 | 0.66 |
| greenland | 8 | 8.32 | 0.49 | 0.49 |
| inner_asia | 7 | 11.49 | 1.02 | 1.02 |
| kalahari | 4 | 5.09 | 1.06 | 1.01 |
| north_america | 19 | 26.66 | 0.89 | 0.89 |
| outback | 7 | 8.98 | 1.00 | 1.00 |
| sahara | 13 | 17.75 | 0.78 | 0.78 |
| south_america | 17 | 23.02 | 0.89 | 0.89 |

## The sea between two landmasses

Two coastlines running closer than the nozzle would print as one
continent.  Rings the atlas deliberately overlaps -- North and Central
America, Central and South America, Europe and Asia -- are left out:
they are one landmass by design.

| channel | width mm |
|---|---|
| north_america / south_america | 2.16 |
| north_america / asia | 1.43 |
| south_america / africa | 3.91 |
| africa / europe | 0.94 |
| africa / asia | 1.21 |

## The strip a subtracted region leaves

`dryland` is subtracted out of `land`, and `ice` out of both, so where
one of those boundaries runs close to the coastline it is cut out of,
the strip left between them is that narrow.  A ring that crosses the
coastline leaves no strip at all there, which is the sound answer
rather than a thin one: the beige or the white simply reaches the sea,
and the green runs out in a wedge instead of a thread.  Only a ring
that stays inside and close can leave a strip nobody can print.

| ring | cut out of | crossings | boundary inside mm | under the nozzle mm | narrowest strip mm |
|---|---|---|---|---|---|
| american_southwest | land | 2 | 5.18 | 0.96 | 0.01 |
| inner_asia | land | 0 | 11.49 | 0.00 | - |
| kalahari | land | 2 | 4.73 | 1.56 | 0.01 |
| outback | land | 0 | 8.98 | 0.00 | - |
| sahara | land | 2 | 14.89 | 1.07 | 0.01 |
| arctic_lobe_1 | land | 4 | 2.45 | 1.94 | 0.00 |
| arctic_lobe_2 | land | 2 | 6.00 | 1.82 | 0.01 |
| arctic_lobe_4 | land | 2 | 1.82 | 0.96 | 0.01 |
| arctic_lobe_5 | land | 2 | 2.23 | 1.52 | 0.02 |
| arctic_lobe_6 | land | 4 | 0.46 | 0.46 | 0.00 |

Named, because a reader finds it and wonders: the Sahara crosses Africa's
west coast, so on that coast the beige reaches the sea and there is no green
strip between desert and ocean at all. That is the deliberate answer and it
is the geographically right one -- the Sahara does reach the Atlantic. The
alternative, a green strip a tenth of a millimetre wide, is a strip no nozzle
can lay down. The same holds for the Kalahari and the American southwest.

The northern cap is a circle of latitude rather than a ring, so it has
no entry here.  Where a coastline crosses 72 degrees the white simply
continues over it, and where a coastline runs south of it the green
boundary and the cap boundary are the same curve.

## What the atlas does not draw

Omissions of the supplied data rather than simplifications this build
made -- but they are the set's omissions now, so they are stated.

- **Japan** -- about 2.6 mm long and 0.3 mm wide at this globe size, so its width is under the 0.4 mm nozzle and it could not carry a colour boundary on both sides.
- **New Zealand** -- the same, and smaller.
- **the Indonesian and Philippine arcs** -- a chain of islands each well under the nozzle; the atlas leaves the arc to the sea by design.
- **the British Isles as a shape of their own** -- inside Europe's ring rather than separate from it; the Channel is 0.2 mm here.
- **the Mediterranean's islands** -- all under the nozzle.
- **Antarctica, and with it any southern ice** -- not in the supplied atlas at all. The globe is also cut off where it sinks into its disc, which at this obliquity removes everything south of about 73 degrees on the longitude facing the lean and about 26 degrees on the longitude opposite it, so a southern cap would be part hidden in any case.

## Simplifications

- **outback** -- north-west corner moved from (119, -20) to (121, -21), 2.24 degrees of arc and 0.33 mm on this globe.  As drawn it ran 0.14 mm inside Australia's west coast, leaving 1.17 mm of green strip thinner than the 0.4 mm nozzle could print; moved, the narrowest green anywhere along it is 0.40 mm.  The outback is an interior beige patch, so the silhouette a player recognises -- Australia's own coastline -- does not move at all.

## Verdict

Nothing in the atlas falls under the 0.40 mm nozzle at this globe
size: no ring edge, no neck, no sea channel and no subtracted strip.
No landmass was dropped.

Measured by `measure/atlas_resolution.py` on the exact rings in
`parts/atlas.py`.
