# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/part_axle.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/measure/component-rounds/axle/r0003/overhang-axle.md`

part_axle.step.py: 60.6 cm2 of surface, grid 0.400 mm, 931 unsupported samples over 7 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | FAIL | 3.9% of the surface faces down that steeply; 3 region(s) need support, 1 bridge, 3 below 1 mm2; worst 115.7 mm2 spanning 22.4 mm |
| bridges within 12 mm | PASS | 1 region(s), longest span 8.0 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | overhang | 115.7 | (-0.4, -0.2, 35.4) | 22.4 | 20.0 |
| 2 | bridge | 14.7 | (-0.6, -6.4, 27.1) | 8.0 | 20.0 |
| 3 | overhang | 2.5 | (5.8, 5.9, 27.1) | 5.3 | 1.2 |
| 4 | overhang | 1.2 | (8.6, 0.0, 47.2) | 0.3 | 10.4 |
| 5 | trace | 0.5 | (-6.3, 5.9, 27.1) | 2.0 | 20.0 |
| 6 | trace | 0.4 | (-8.4, 2.1, 27.1) | 0.4 | 20.0 |
| 7 | trace | 0.1 | (6.1, -6.1, 47.2) | 0.0 | 10.4 |

RESULT: NEEDS SUPPORT

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
