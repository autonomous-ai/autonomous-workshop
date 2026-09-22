# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_07_rear.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_07_rear/r0003/overhang-body_07_rear.md`

part_body_07_rear.step.py: 10.3 cm2 of surface, grid 0.400 mm, 35 unsupported samples over 3 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | FAIL | 22.9% of the surface faces down that steeply; 1 region(s) need support, 1 bridge, 1 below 1 mm2; worst 1.1 mm2 spanning 1.0 mm |
| bridges within 12 mm | PASS | 1 region(s), longest span 2.2 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 1.3 | (3.6, 0.1, 1.5) | 2.2 | 1.6 |
| 2 | overhang | 1.1 | (-4.1, -0.8, 0.3) | 1.0 | 1.6 |
| 3 | trace | 0.0 | (2.6, -5.3, 3.1) | 0.0 | 0.8 |

RESULT: NEEDS SUPPORT

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
