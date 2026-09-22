# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_head_rear.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/head_rear/r0002/overhang-head_rear.md`

part_head_rear.step.py: 88.0 cm2 of surface, grid 0.400 mm, 316 unsupported samples over 4 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 27.7% of the surface faces down that steeply; 0 region(s) need support, 3 bridge, 1 below 1 mm2 |
| bridges within 12 mm | PASS | 3 region(s), longest span 3.3 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 14.8 | (0.0, -19.2, 11.3) | 3.3 | 7.6 |
| 2 | bridge | 8.9 | (16.9, -16.5, 12.0) | 2.7 | 5.6 |
| 3 | bridge | 8.9 | (-16.9, -16.4, 11.9) | 2.7 | 6.0 |
| 4 | trace | 0.2 | (3.5, 9.6, 27.2) | 1.0 | 1.6 |

RESULT: prints unsupported

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
