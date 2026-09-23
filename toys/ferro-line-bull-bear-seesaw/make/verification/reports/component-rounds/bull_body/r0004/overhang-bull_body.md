# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_bull_body.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/bull_body/r0004/overhang-bull_body.md`

part_bull_body.step.py: 163.9 cm2 of surface, grid 0.400 mm, 1635 unsupported samples over 9 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | FAIL | 25.3% of the surface faces down that steeply; 1 region(s) need support, 8 bridge, 0 below 1 mm2; worst 84.3 mm2 spanning 3.0 mm |
| bridges within 12 mm | PASS | 8 region(s), longest span 7.3 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | overhang | 84.3 | (36.5, -11.7, 7.8) | 3.0 | 8.8 |
| 2 | bridge | 27.6 | (9.8, -12.1, 1.3) | 5.3 | 2.4 |
| 3 | bridge | 23.7 | (19.2, -21.1, 1.3) | 7.2 | 2.4 |
| 4 | bridge | 23.7 | (-4.7, -21.0, 1.3) | 7.3 | 2.4 |
| 5 | bridge | 21.0 | (-26.9, -27.7, 20.6) | 2.7 | 20.0 |
| 6 | bridge | 20.6 | (27.2, -27.1, 20.6) | 2.6 | 20.0 |
| 7 | bridge | 19.5 | (0.1, 29.2, 27.2) | 2.7 | 20.0 |
| 8 | bridge | 7.6 | (-26.9, -30.5, 13.0) | 2.1 | 14.0 |

RESULT: NEEDS SUPPORT

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
