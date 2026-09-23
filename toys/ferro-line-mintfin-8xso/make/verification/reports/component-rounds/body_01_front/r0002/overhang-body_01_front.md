# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_01_front.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_01_front/r0002/overhang-body_01_front.md`

part_body_01_front.step.py: 45.5 cm2 of surface, grid 0.400 mm, 633 unsupported samples over 5 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | FAIL | 44.0% of the surface faces down that steeply; 3 region(s) need support, 1 bridge, 1 below 1 mm2; worst 89.2 mm2 spanning 4.5 mm |
| bridges within 12 mm | PASS | 1 region(s), longest span 1.2 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | overhang | 89.2 | (0.0, -15.8, 2.9) | 4.5 | 1.2 |
| 2 | bridge | 3.1 | (-0.0, 21.1, 1.8) | 1.2 | 3.2 |
| 3 | overhang | 1.2 | (-21.7, -7.1, 2.5) | 0.8 | 4.0 |
| 4 | overhang | 1.2 | (21.6, -7.0, 2.5) | 1.0 | 4.0 |
| 5 | trace | 0.5 | (0.0, 8.3, 0.2) | 0.5 | 1.2 |

RESULT: NEEDS SUPPORT

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
