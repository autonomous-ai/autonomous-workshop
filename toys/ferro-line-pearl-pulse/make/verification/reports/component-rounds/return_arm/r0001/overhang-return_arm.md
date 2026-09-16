# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_return_arm.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/return_arm/r0001/overhang-return_arm.md`

part_return_arm.step.py: 2.8 cm2 of surface, grid 0.400 mm, 292 unsupported samples over 1 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | FAIL | 21.2% of the surface faces down that steeply; 1 region(s) need support, 0 bridge, 0 below 1 mm2; worst 46.2 mm2 spanning 4.7 mm |
| bridges within 12 mm | PASS | 0 region(s), longest span 0.0 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | overhang | 46.2 | (-0.0, -80.0, 0.6) | 4.7 | 1.6 |

RESULT: NEEDS SUPPORT

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
