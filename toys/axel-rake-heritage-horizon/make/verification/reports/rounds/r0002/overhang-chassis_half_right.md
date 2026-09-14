# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/heritage/part_chassis_half_right.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/heritage/measure/rounds/r0002/overhang-chassis_half_right.md`

part_chassis_half_right.step.py: 108.3 cm2 of surface, grid 0.400 mm, 358 unsupported samples over 4 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 25.1% of the surface faces down that steeply; 0 region(s) need support, 2 bridge, 2 below 1 mm2 |
| bridges within 12 mm | PASS | 2 region(s), longest span 6.0 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 53.5 | (35.6, 66.2, 5.2) | 6.0 | 6.4 |
| 2 | bridge | 2.4 | (9.7, 33.1, 15.4) | 1.0 | 2.4 |
| 3 | trace | 0.7 | (13.6, 37.9, 15.4) | 0.6 | 2.4 |
| 4 | trace | 0.1 | (-10.0, 32.7, 15.4) | 0.0 | 2.4 |

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
