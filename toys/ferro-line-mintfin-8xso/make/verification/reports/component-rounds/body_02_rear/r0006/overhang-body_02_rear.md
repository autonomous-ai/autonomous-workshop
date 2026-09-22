# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_02_rear.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_02_rear/r0006/overhang-body_02_rear.md`

part_body_02_rear.step.py: 47.4 cm2 of surface, grid 0.400 mm, 18 unsupported samples over 4 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 40.1% of the surface faces down that steeply; 0 region(s) need support, 0 bridge, 4 below 1 mm2 |
| bridges within 12 mm | PASS | 0 region(s), longest span 0.0 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | trace | 0.4 | (3.3, -5.5, 4.8) | 1.2 | 1.6 |
| 2 | trace | 0.2 | (3.1, -12.2, 4.8) | 1.0 | 1.2 |
| 3 | trace | 0.1 | (-3.4, -5.6, 4.8) | 0.8 | 1.2 |
| 4 | trace | 0.0 | (0.0, -15.3, 0.4) | 0.0 | 1.6 |

RESULT: prints unsupported

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
