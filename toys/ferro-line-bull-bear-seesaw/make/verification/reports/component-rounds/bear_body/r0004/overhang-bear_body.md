# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_bear_body.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/bear_body/r0004/overhang-bear_body.md`

part_bear_body.step.py: 160.8 cm2 of surface, grid 0.400 mm, 958 unsupported samples over 8 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 25.5% of the surface faces down that steeply; 0 region(s) need support, 6 bridge, 2 below 1 mm2 |
| bridges within 12 mm | PASS | 6 region(s), longest span 6.9 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 36.0 | (-24.9, -31.2, 1.3) | 6.3 | 2.4 |
| 2 | bridge | 35.8 | (25.2, -31.2, 1.3) | 6.9 | 2.4 |
| 3 | bridge | 23.8 | (0.1, 30.5, 27.2) | 2.7 | 20.0 |
| 4 | bridge | 20.3 | (-26.9, -24.5, 20.6) | 2.5 | 16.4 |
| 5 | bridge | 19.4 | (27.2, -24.5, 20.6) | 2.4 | 6.4 |
| 6 | bridge | 4.4 | (-11.0, -2.9, 1.3) | 0.9 | 2.4 |
| 7 | trace | 0.2 | (-30.3, -26.5, 4.0) | 0.4 | 5.2 |
| 8 | trace | 0.1 | (30.4, -26.5, 4.0) | 0.0 | 5.2 |

RESULT: prints unsupported

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
