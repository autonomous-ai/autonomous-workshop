# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_circle_asteroid.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/circle_asteroid/r0001/overhang-circle_asteroid.md`

part_circle_asteroid.step.py: 16.7 cm2 of surface, grid 0.400 mm, 105 unsupported samples over 6 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | FAIL | 22.9% of the surface faces down that steeply; 2 region(s) need support, 0 bridge, 4 below 1 mm2; worst 2.7 mm2 spanning 1.5 mm |
| bridges within 12 mm | PASS | 0 region(s), longest span 0.0 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | overhang | 2.7 | (-2.1, -5.6, 12.3) | 1.5 | 2.8 |
| 2 | overhang | 1.3 | (2.0, -5.5, 8.9) | 0.9 | 5.6 |
| 3 | trace | 0.5 | (1.9, -5.2, 16.1) | 0.7 | 2.4 |
| 4 | trace | 0.0 | (0.0, -10.9, 3.1) | 0.0 | 4.0 |
| 5 | trace | 0.0 | (-1.6, 10.9, 3.1) | 0.0 | 4.0 |
| 6 | trace | 0.0 | (1.8, 10.9, 3.1) | 0.0 | 4.0 |

RESULT: NEEDS SUPPORT

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
