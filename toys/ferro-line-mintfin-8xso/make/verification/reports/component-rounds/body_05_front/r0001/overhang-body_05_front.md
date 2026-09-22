# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_05_front.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_05_front/r0001/overhang-body_05_front.md`

part_body_05_front.step.py: 22.2 cm2 of surface, grid 0.400 mm, 204 unsupported samples over 2 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | FAIL | 41.3% of the surface faces down that steeply; 1 region(s) need support, 1 bridge, 0 below 1 mm2; worst 24.1 mm2 spanning 2.2 mm |
| bridges within 12 mm | PASS | 1 region(s), longest span 1.6 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | overhang | 24.1 | (0.1, -11.5, 3.2) | 2.2 | 1.2 |
| 2 | bridge | 5.2 | (-0.1, 14.7, 1.8) | 1.6 | 3.2 |

RESULT: NEEDS SUPPORT

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
