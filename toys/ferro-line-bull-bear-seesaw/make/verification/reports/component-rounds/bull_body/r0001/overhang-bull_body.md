# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_bull_body.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/bull_body/r0001/overhang-bull_body.md`

part_bull_body.step.py: 190.7 cm2 of surface, grid 0.400 mm, 10521 unsupported samples over 5 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | FAIL | 28.4% of the surface faces down that steeply; 2 region(s) need support, 3 bridge, 0 below 1 mm2; worst 1434.1 mm2 spanning 45.9 mm |
| bridges within 12 mm | PASS | 3 region(s), longest span 7.1 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | overhang | 1434.1 | (0.2, 8.2, 11.2) | 45.9 | 12.4 |
| 2 | overhang | 147.8 | (0.1, 30.5, 16.4) | 11.5 | 17.6 |
| 3 | bridge | 26.9 | (9.8, -10.8, 1.3) | 5.2 | 2.4 |
| 4 | bridge | 24.6 | (-4.9, -19.9, 1.3) | 7.1 | 2.4 |
| 5 | bridge | 24.3 | (19.4, -19.9, 1.3) | 7.1 | 2.4 |

RESULT: NEEDS SUPPORT

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
