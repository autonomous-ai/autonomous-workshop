# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_bull_body.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/bull_body/r0005/overhang-bull_body.md`

part_bull_body.step.py: 159.8 cm2 of surface, grid 0.400 mm, 1126 unsupported samples over 8 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 25.5% of the surface faces down that steeply; 0 region(s) need support, 8 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 8 region(s), longest span 7.5 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 26.0 | (10.1, -12.1, 1.3) | 5.3 | 2.4 |
| 2 | bridge | 24.0 | (-4.7, -21.2, 1.3) | 7.5 | 2.4 |
| 3 | bridge | 24.0 | (19.1, -21.1, 1.3) | 7.3 | 2.4 |
| 4 | bridge | 22.4 | (0.1, 29.3, 27.2) | 2.7 | 20.0 |
| 5 | bridge | 21.1 | (27.1, -27.5, 20.6) | 2.6 | 20.0 |
| 6 | bridge | 21.0 | (-26.9, -27.3, 20.6) | 2.6 | 20.0 |
| 7 | bridge | 7.6 | (-27.0, -30.4, 13.0) | 2.2 | 14.0 |
| 8 | bridge | 7.6 | (27.0, -30.4, 13.0) | 2.0 | 14.0 |

RESULT: prints unsupported

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
