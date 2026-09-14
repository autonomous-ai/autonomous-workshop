# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_canopy_rear_adapter_left.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0006/overhang-canopy_rear_adapter_left.md`

part_canopy_rear_adapter_left.step.py: 44.6 cm2 of surface, grid 0.400 mm, 940 unsupported samples over 6 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 10.3% of the surface faces down that steeply; 0 region(s) need support, 6 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 6 region(s), longest span 7.7 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 73.8 | (5.2, 0.3, 14.0) | 7.7 | 15.2 |
| 2 | bridge | 23.9 | (5.2, 16.2, 31.0) | 6.9 | 20.0 |
| 3 | bridge | 19.3 | (10.7, 0.2, 8.9) | 3.0 | 9.2 |
| 4 | bridge | 10.3 | (-0.5, -0.0, 8.6) | 3.2 | 11.6 |
| 5 | bridge | 9.7 | (-0.3, 13.7, 12.0) | 0.6 | 13.2 |
| 6 | bridge | 2.1 | (10.9, -7.4, 12.0) | 0.8 | 13.2 |

RESULT: prints unsupported

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
