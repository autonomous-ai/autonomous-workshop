# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_04_rear.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_04_rear/r0002/overhang-body_04_rear.md`

part_body_04_rear.step.py: 35.8 cm2 of surface, grid 0.400 mm, 11 unsupported samples over 2 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 39.4% of the surface faces down that steeply; 0 region(s) need support, 0 bridge, 2 below 1 mm2 |
| bridges within 12 mm | PASS | 0 region(s), longest span 0.0 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | trace | 0.4 | (3.2, -4.8, 4.9) | 1.1 | 1.6 |
| 2 | trace | 0.1 | (3.5, -10.9, 4.9) | 0.1 | 0.8 |

RESULT: prints unsupported

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
