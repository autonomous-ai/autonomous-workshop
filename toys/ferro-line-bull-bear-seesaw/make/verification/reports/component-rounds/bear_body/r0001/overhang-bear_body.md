# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_bear_body.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/bear_body/r0001/overhang-bear_body.md`

part_bear_body.step.py: 190.4 cm2 of surface, grid 0.400 mm, 10903 unsupported samples over 6 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | FAIL | 28.9% of the surface faces down that steeply; 2 region(s) need support, 4 bridge, 0 below 1 mm2; worst 1441.5 mm2 spanning 45.9 mm |
| bridges within 12 mm | PASS | 4 region(s), longest span 8.0 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | overhang | 1441.5 | (0.1, 9.1, 11.2) | 45.9 | 12.4 |
| 2 | overhang | 147.1 | (-0.0, 31.5, 16.4) | 11.5 | 17.6 |
| 3 | bridge | 49.0 | (-10.7, -17.2, 1.3) | 8.0 | 2.4 |
| 4 | bridge | 36.3 | (-24.8, -30.1, 1.3) | 6.8 | 2.4 |
| 5 | bridge | 36.1 | (25.2, -30.1, 1.3) | 6.9 | 2.4 |
| 6 | bridge | 4.2 | (-10.4, -1.7, 1.3) | 0.8 | 2.4 |

RESULT: NEEDS SUPPORT

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
