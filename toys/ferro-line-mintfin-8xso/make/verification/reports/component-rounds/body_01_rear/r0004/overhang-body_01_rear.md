# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_01_rear.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_01_rear/r0004/overhang-body_01_rear.md`

part_body_01_rear.step.py: 45.0 cm2 of surface, grid 0.400 mm, 36 unsupported samples over 5 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | FAIL | 40.9% of the surface faces down that steeply; 1 region(s) need support, 0 bridge, 4 below 1 mm2; worst 2.7 mm2 spanning 0.1 mm |
| bridges within 12 mm | PASS | 0 region(s), longest span 0.0 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | overhang | 2.7 | (-1.8, -20.9, 0.2) | 0.1 | 1.2 |
| 2 | trace | 0.4 | (3.5, -4.8, 4.1) | 1.1 | 1.6 |
| 3 | trace | 0.3 | (9.2, -21.0, 0.2) | 0.0 | 1.2 |
| 4 | trace | 0.2 | (-3.5, -4.8, 4.1) | 0.9 | 0.8 |
| 5 | trace | 0.2 | (3.6, -11.6, 4.1) | 0.9 | 0.8 |

RESULT: NEEDS SUPPORT

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
