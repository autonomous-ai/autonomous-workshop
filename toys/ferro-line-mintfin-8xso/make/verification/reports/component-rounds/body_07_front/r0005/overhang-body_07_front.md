# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_07_front.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_07_front/r0005/overhang-body_07_front.md`

part_body_07_front.step.py: 7.5 cm2 of surface, grid 0.400 mm, 192 unsupported samples over 2 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | FAIL | 30.2% of the surface faces down that steeply; 1 region(s) need support, 1 bridge, 0 below 1 mm2; worst 6.2 mm2 spanning 1.1 mm |
| bridges within 12 mm | PASS | 1 region(s), longest span 5.6 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 10.2 | (-0.2, -2.3, 0.8) | 5.6 | 2.4 |
| 2 | overhang | 6.2 | (-0.1, -9.0, 0.8) | 1.1 | 2.4 |

RESULT: NEEDS SUPPORT

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
