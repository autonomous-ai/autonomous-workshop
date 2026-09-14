# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_canopy_end_join_rear.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0006/overhang-canopy_end_join_rear.md`

part_canopy_end_join_rear.step.py: 77.4 cm2 of surface, grid 0.400 mm, 1096 unsupported samples over 4 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 20.5% of the surface faces down that steeply; 0 region(s) need support, 4 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 4 region(s), longest span 9.2 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 81.1 | (-15.1, 13.5, 6.2) | 9.2 | 7.6 |
| 2 | bridge | 78.7 | (15.1, 13.5, 6.2) | 9.1 | 7.6 |
| 3 | bridge | 2.1 | (-3.9, -7.3, 77.0) | 0.4 | 20.0 |
| 4 | bridge | 1.6 | (3.5, -7.2, 77.0) | 0.6 | 20.0 |

RESULT: prints unsupported

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
