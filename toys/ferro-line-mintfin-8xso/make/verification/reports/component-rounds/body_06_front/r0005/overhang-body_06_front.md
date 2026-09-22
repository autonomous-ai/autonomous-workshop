# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_06_front.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_06_front/r0005/overhang-body_06_front.md`

part_body_06_front.step.py: 12.9 cm2 of surface, grid 0.400 mm, 38 unsupported samples over 2 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 37.0% of the surface faces down that steeply; 0 region(s) need support, 1 bridge, 1 below 1 mm2 |
| bridges within 12 mm | PASS | 1 region(s), longest span 2.1 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 2.8 | (-0.0, 3.5, 1.6) | 2.1 | 3.2 |
| 2 | trace | 0.3 | (1.1, -0.9, 2.0) | 2.9 | 0.8 |

RESULT: prints unsupported

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
