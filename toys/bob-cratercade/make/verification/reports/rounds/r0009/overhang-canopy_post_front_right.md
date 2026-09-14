# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_canopy_post_front_right.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0009/overhang-canopy_post_front_right.md`

part_canopy_post_front_right.step.py: 104.8 cm2 of surface, grid 0.400 mm, 696 unsupported samples over 5 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 2.7% of the surface faces down that steeply; 0 region(s) need support, 5 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 5 region(s), longest span 9.8 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 37.7 | (-4.2, 0.2, 70.3) | 9.8 | 20.0 |
| 2 | bridge | 24.0 | (-4.8, 0.2, 92.0) | 7.0 | 20.0 |
| 3 | bridge | 20.5 | (-10.7, 0.1, 9.0) | 3.0 | 11.2 |
| 4 | bridge | 10.3 | (0.5, 0.0, 8.6) | 3.1 | 9.2 |
| 5 | bridge | 2.1 | (-10.8, 7.6, 73.0) | 0.6 | 20.0 |

RESULT: prints unsupported

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
