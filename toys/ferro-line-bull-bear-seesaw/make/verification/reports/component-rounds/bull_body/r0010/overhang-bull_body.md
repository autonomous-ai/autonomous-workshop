# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_bull_body.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/bull_body/r0010/overhang-bull_body.md`

part_bull_body.step.py: 155.5 cm2 of surface, grid 0.400 mm, 1503 unsupported samples over 11 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 23.4% of the surface faces down that steeply; 0 region(s) need support, 10 bridge, 1 below 1 mm2 |
| bridges within 12 mm | PASS | 10 region(s), longest span 11.4 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 90.9 | (-32.8, -17.4, 1.2) | 11.4 | 2.4 |
| 2 | bridge | 23.5 | (-10.9, 33.2, 27.2) | 2.7 | 20.0 |
| 3 | bridge | 22.7 | (15.1, -21.6, 1.9) | 7.6 | 5.2 |
| 4 | bridge | 20.0 | (16.2, -21.8, 20.6) | 2.4 | 20.0 |
| 5 | bridge | 18.3 | (-37.8, -21.6, 20.6) | 2.7 | 16.4 |
| 6 | bridge | 17.9 | (-13.5, -20.3, 1.2) | 3.9 | 2.4 |
| 7 | bridge | 14.6 | (10.1, 20.9, 1.2) | 1.4 | 2.4 |
| 8 | bridge | 14.4 | (21.1, -14.2, 1.2) | 4.7 | 2.4 |

RESULT: prints unsupported

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
