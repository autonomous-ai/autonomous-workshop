# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_bull_body.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/bull_body/r0006/overhang-bull_body.md`

part_bull_body.step.py: 161.6 cm2 of surface, grid 0.400 mm, 926 unsupported samples over 9 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | FAIL | 25.0% of the surface faces down that steeply; 2 region(s) need support, 5 bridge, 2 below 1 mm2; worst 23.3 mm2 spanning 3.6 mm |
| bridges within 12 mm | PASS | 5 region(s), longest span 3.4 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | overhang | 23.3 | (-27.0, -23.6, 13.0) | 3.6 | 8.8 |
| 2 | overhang | 22.9 | (27.0, -23.6, 13.0) | 3.6 | 8.8 |
| 3 | bridge | 21.7 | (0.2, 29.4, 27.2) | 2.7 | 20.0 |
| 4 | bridge | 21.3 | (-26.9, -25.6, 20.6) | 2.6 | 20.0 |
| 5 | bridge | 20.7 | (27.0, -25.6, 20.6) | 2.6 | 20.0 |
| 6 | bridge | 13.0 | (-4.9, -23.3, 1.3) | 2.9 | 2.4 |
| 7 | bridge | 12.6 | (19.0, -23.4, 1.3) | 3.4 | 2.4 |
| 8 | trace | 0.2 | (-26.9, -29.4, 13.0) | 0.1 | 14.0 |

RESULT: NEEDS SUPPORT

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
