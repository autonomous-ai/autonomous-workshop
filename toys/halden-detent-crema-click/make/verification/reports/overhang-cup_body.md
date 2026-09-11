# Overhang and support

`artifacts/make/r0001/product/cad/crema_click/part_cup_body.step.py --angle 45.0 --report artifacts/make/r0001/product/cad/crema_click/measure/overhang-cup_body.md`

part_cup_body.step.py: 216.9 cm2 of surface, grid 0.400 mm, 4416 unsupported samples over 12 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 11.4% of the surface faces down that steeply; 0 region(s) need support, 12 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 12 region(s), longest span 10.0 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 79.2 | (-13.1, 13.6, 10.4) | 9.7 | 11.6 |
| 2 | bridge | 78.8 | (13.6, -13.2, 10.4) | 10.0 | 11.6 |
| 3 | bridge | 78.2 | (-13.2, -13.3, 10.4) | 10.0 | 11.6 |
| 4 | bridge | 77.8 | (13.6, 13.6, 10.4) | 9.6 | 11.6 |
| 5 | bridge | 63.7 | (-23.1, 0.2, 5.6) | 5.6 | 6.8 |
| 6 | bridge | 52.2 | (11.3, 20.9, 5.6) | 7.5 | 6.8 |
| 7 | bridge | 50.9 | (0.2, 14.7, 19.3) | 5.7 | 20.4 |
| 8 | bridge | 50.7 | (11.1, -20.9, 5.6) | 7.3 | 6.8 |

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.

RESULT: prints unsupported
