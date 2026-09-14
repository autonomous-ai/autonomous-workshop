# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/heritage/part_tank_cover.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/heritage/measure/component-rounds/tank_cover/r0001/overhang-tank_cover.md`

part_tank_cover.step.py: 37.3 cm2 of surface, grid 0.400 mm, 267 unsupported samples over 6 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | FAIL | 25.8% of the surface faces down that steeply; 3 region(s) need support, 2 bridge, 1 below 1 mm2; worst 7.2 mm2 spanning 1.9 mm |
| bridges within 12 mm | PASS | 2 region(s), longest span 3.1 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 8.6 | (0.3, 0.3, 3.2) | 3.1 | 4.4 |
| 2 | bridge | 8.4 | (18.3, 0.2, 3.2) | 3.1 | 4.4 |
| 3 | overhang | 7.2 | (8.0, -13.1, 0.5) | 1.9 | 2.0 |
| 4 | overhang | 5.9 | (7.7, 13.2, 0.5) | 1.6 | 2.0 |
| 5 | overhang | 1.4 | (-18.3, 0.2, 0.4) | 0.4 | 1.6 |
| 6 | trace | 0.6 | (28.2, -1.6, 0.4) | 0.1 | 1.6 |

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
