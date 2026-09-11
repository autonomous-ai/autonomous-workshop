# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/crema_click/part_cup_body.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/crema_click/measure/rounds/r0004/overhang-cup_body.md`

part_cup_body.step.py: 211.7 cm2 of surface, grid 0.400 mm, 5188 unsupported samples over 10 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | FAIL | 11.5% of the surface faces down that steeply; 1 region(s) need support, 9 bridge, 0 below 1 mm2; worst 136.7 mm2 spanning 54.6 mm |
| bridges within 12 mm | PASS | 9 region(s), longest span 10.1 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | overhang | 136.7 | (-2.1, -0.1, 0.8) | 54.6 | 2.8 |
| 2 | bridge | 89.8 | (-22.9, 0.2, 4.6) | 7.8 | 5.6 |
| 3 | bridge | 79.0 | (-13.3, 13.6, 10.4) | 9.7 | 11.6 |
| 4 | bridge | 78.9 | (13.5, -13.3, 10.4) | 10.1 | 11.6 |
| 5 | bridge | 78.8 | (-13.2, -13.2, 10.4) | 10.1 | 11.6 |
| 6 | bridge | 78.2 | (13.5, 13.6, 10.4) | 9.7 | 11.6 |
| 7 | bridge | 69.8 | (11.1, 21.0, 4.6) | 9.0 | 5.6 |
| 8 | bridge | 67.3 | (11.2, -20.9, 4.6) | 8.7 | 5.6 |

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
