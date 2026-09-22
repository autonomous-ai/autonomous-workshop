# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_05_rear.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_05_rear/r0003/overhang-body_05_rear.md`

part_body_05_rear.step.py: 23.5 cm2 of surface, grid 0.400 mm, 17 unsupported samples over 4 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 36.5% of the surface faces down that steeply; 0 region(s) need support, 0 bridge, 4 below 1 mm2 |
| bridges within 12 mm | PASS | 0 region(s), longest span 0.0 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | trace | 0.4 | (3.2, -3.1, 3.9) | 1.1 | 1.6 |
| 2 | trace | 0.2 | (-3.1, -3.0, 3.9) | 1.2 | 1.2 |
| 3 | trace | 0.1 | (2.8, -9.5, 3.9) | 0.3 | 1.2 |
| 4 | trace | 0.0 | (-3.3, -9.0, 3.9) | 0.0 | 0.8 |

RESULT: prints unsupported

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
