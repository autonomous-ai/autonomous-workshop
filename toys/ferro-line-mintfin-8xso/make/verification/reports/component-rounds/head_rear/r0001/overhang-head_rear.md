# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_head_rear.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/head_rear/r0001/overhang-head_rear.md`

part_head_rear.step.py: 88.3 cm2 of surface, grid 0.400 mm, 737 unsupported samples over 6 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | FAIL | 28.3% of the surface faces down that steeply; 2 region(s) need support, 3 bridge, 1 below 1 mm2; worst 33.9 mm2 spanning 2.7 mm |
| bridges within 12 mm | PASS | 3 region(s), longest span 3.0 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | overhang | 33.9 | (-30.1, 0.1, 10.0) | 2.7 | 2.4 |
| 2 | overhang | 31.2 | (30.2, 0.2, 10.0) | 2.6 | 2.4 |
| 3 | bridge | 14.8 | (0.0, -19.1, 11.3) | 3.0 | 7.6 |
| 4 | bridge | 8.9 | (16.9, -16.4, 12.0) | 2.7 | 5.6 |
| 5 | bridge | 8.9 | (-16.9, -16.5, 12.0) | 2.7 | 6.0 |
| 6 | trace | 0.2 | (3.6, 9.4, 27.2) | 0.9 | 1.6 |

RESULT: NEEDS SUPPORT

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
