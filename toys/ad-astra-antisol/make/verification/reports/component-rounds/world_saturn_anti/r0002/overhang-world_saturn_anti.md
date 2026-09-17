# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_world_saturn_anti.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/world_saturn_anti/r0002/overhang-world_saturn_anti.md`

part_world_saturn_anti.step.py: 44.1 cm2 of surface, grid 0.400 mm, 59 unsupported samples over 5 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | FAIL | 20.7% of the surface faces down that steeply; 2 region(s) need support, 1 bridge, 2 below 1 mm2; worst 3.1 mm2 spanning 1.3 mm |
| bridges within 12 mm | PASS | 1 region(s), longest span 9.3 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | overhang | 3.1 | (-13.3, 0.0, 7.6) | 1.3 | 3.2 |
| 2 | overhang | 1.8 | (-8.1, -12.1, 10.9) | 9.5 | 9.2 |
| 3 | bridge | 1.7 | (-8.6, 11.7, 10.6) | 9.3 | 8.0 |
| 4 | trace | 0.1 | (-1.1, 15.9, 14.1) | 0.0 | 9.2 |
| 5 | trace | 0.0 | (1.8, -15.9, 16.0) | 0.0 | 11.2 |

RESULT: NEEDS SUPPORT

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
