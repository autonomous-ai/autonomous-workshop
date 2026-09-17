# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_world_saturn_sol.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/world_saturn_sol/r0007/overhang-world_saturn_sol.md`

part_world_saturn_sol.step.py: 41.4 cm2 of surface, grid 0.400 mm, 86 unsupported samples over 3 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | FAIL | 20.7% of the surface faces down that steeply; 1 region(s) need support, 0 bridge, 2 below 1 mm2; worst 1.0 mm2 spanning 24.8 mm |
| bridges within 12 mm | PASS | 0 region(s), longest span 0.0 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | overhang | 1.0 | (1.4, -7.5, 14.5) | 24.8 | 17.2 |
| 2 | trace | 0.4 | (-8.8, 9.7, 19.7) | 12.1 | 17.2 |
| 3 | trace | 0.1 | (3.9, 14.1, 13.2) | 1.5 | 9.2 |

RESULT: NEEDS SUPPORT

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
