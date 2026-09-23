# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_bear_body.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/bear_body/r0003/overhang-bear_body.md`

part_bear_body.step.py: 161.2 cm2 of surface, grid 0.400 mm, 1286 unsupported samples over 8 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | FAIL | 25.8% of the surface faces down that steeply; 2 region(s) need support, 6 bridge, 0 below 1 mm2; worst 23.3 mm2 spanning 6.2 mm |
| bridges within 12 mm | PASS | 6 region(s), longest span 6.9 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 36.0 | (-24.9, -31.2, 1.3) | 6.3 | 2.4 |
| 2 | bridge | 35.8 | (25.2, -31.2, 1.3) | 6.9 | 2.4 |
| 3 | bridge | 23.8 | (0.1, 30.5, 27.2) | 2.7 | 20.0 |
| 4 | overhang | 23.3 | (-27.3, -22.7, 13.0) | 6.2 | 14.0 |
| 5 | overhang | 22.6 | (27.0, -22.6, 13.0) | 5.9 | 14.0 |
| 6 | bridge | 20.2 | (27.1, -24.5, 20.6) | 2.4 | 6.4 |
| 7 | bridge | 19.7 | (-26.8, -24.5, 20.6) | 2.4 | 6.4 |
| 8 | bridge | 4.4 | (-11.0, -2.9, 1.3) | 0.9 | 2.4 |

RESULT: NEEDS SUPPORT

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
