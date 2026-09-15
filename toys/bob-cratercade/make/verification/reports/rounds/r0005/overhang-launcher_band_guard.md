# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_launcher_band_guard.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0005/overhang-launcher_band_guard.md`

part_launcher_band_guard.step.py: 75.9 cm2 of surface, grid 0.400 mm, 288 unsupported samples over 2 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 39.7% of the surface faces down that steeply; 0 region(s) need support, 2 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 2 region(s), longest span 8.5 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 19.9 | (11.8, 132.3, 0.8) | 8.4 | 3.6 |
| 2 | bridge | 19.4 | (18.4, 7.3, 0.8) | 8.5 | 3.6 |

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
