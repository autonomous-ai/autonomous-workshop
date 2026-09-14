# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/heritage/part_chassis_half.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/heritage/measure/component-rounds/chassis_half/r0004/overhang-chassis_half.md`

part_chassis_half.step.py: 110.0 cm2 of surface, grid 0.400 mm, 636 unsupported samples over 5 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | FAIL | 25.4% of the surface faces down that steeply; 1 region(s) need support, 2 bridge, 2 below 1 mm2; worst 44.6 mm2 spanning 5.0 mm |
| bridges within 12 mm | PASS | 2 region(s), longest span 5.9 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 52.7 | (35.8, -66.1, 5.2) | 5.9 | 6.4 |
| 2 | overhang | 44.6 | (-32.9, -31.7, 11.4) | 5.0 | 4.4 |
| 3 | bridge | 2.3 | (10.1, -32.9, 15.4) | 0.8 | 2.4 |
| 4 | trace | 0.7 | (13.8, -37.7, 15.4) | 0.4 | 2.4 |
| 5 | trace | 0.1 | (-9.9, -32.8, 15.4) | 0.0 | 2.4 |

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
