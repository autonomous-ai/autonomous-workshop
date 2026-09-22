# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_leg_left.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/leg_left/r0001/overhang-leg_left.md`

part_leg_left.step.py: 20.1 cm2 of surface, grid 0.400 mm, 400 unsupported samples over 4 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | FAIL | 20.0% of the surface faces down that steeply; 1 region(s) need support, 3 bridge, 0 below 1 mm2; worst 2.8 mm2 spanning 1.0 mm |
| bridges within 12 mm | PASS | 3 region(s), longest span 2.2 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 4.8 | (-0.0, -10.2, 4.1) | 1.8 | 5.6 |
| 2 | bridge | 4.6 | (-6.0, -8.6, 4.2) | 1.5 | 5.6 |
| 3 | bridge | 4.5 | (6.0, -9.0, 4.0) | 2.2 | 5.6 |
| 4 | overhang | 2.8 | (13.1, 6.6, 15.0) | 1.0 | 16.0 |

RESULT: NEEDS SUPPORT

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
