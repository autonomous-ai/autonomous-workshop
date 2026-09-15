# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_canopy_post_middle.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0004/overhang-canopy_post_middle.md`

part_canopy_post_middle.step.py: 100.4 cm2 of surface, grid 0.400 mm, 678 unsupported samples over 4 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 2.8% of the surface faces down that steeply; 0 region(s) need support, 4 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 4 region(s), longest span 9.6 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 37.6 | (4.8, 0.2, 70.3) | 9.6 | 20.0 |
| 2 | bridge | 24.5 | (5.2, 0.1, 92.0) | 6.9 | 20.0 |
| 3 | bridge | 19.6 | (10.7, 0.1, 9.0) | 2.9 | 9.2 |
| 4 | bridge | 10.3 | (-0.5, 0.0, 8.6) | 3.1 | 11.6 |

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
