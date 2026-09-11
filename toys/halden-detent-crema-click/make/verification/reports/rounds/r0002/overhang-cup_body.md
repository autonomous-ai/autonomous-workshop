# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/crema_click/part_cup_body.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/crema_click/measure/rounds/r0002/overhang-cup_body.md`

part_cup_body.step.py: 214.0 cm2 of surface, grid 0.400 mm, 3685 unsupported samples over 9 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 12.3% of the surface faces down that steeply; 0 region(s) need support, 9 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 9 region(s), longest span 10.1 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 78.3 | (13.5, 13.7, 10.4) | 9.7 | 11.6 |
| 2 | bridge | 78.1 | (-13.4, 13.6, 10.4) | 9.8 | 11.6 |
| 3 | bridge | 78.0 | (-13.2, -13.2, 10.4) | 10.0 | 11.6 |
| 4 | bridge | 77.9 | (13.5, -13.3, 10.4) | 10.1 | 11.6 |
| 5 | bridge | 52.5 | (-22.6, 0.2, 4.1) | 5.2 | 5.2 |
| 6 | bridge | 51.2 | (0.1, 14.8, 19.3) | 5.7 | 20.4 |
| 7 | bridge | 49.0 | (0.1, -14.6, 19.3) | 5.9 | 20.4 |
| 8 | bridge | 40.6 | (11.0, 20.4, 4.1) | 7.1 | 5.2 |

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
