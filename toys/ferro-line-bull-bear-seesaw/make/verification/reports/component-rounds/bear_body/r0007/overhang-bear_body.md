# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_bear_body.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/bear_body/r0007/overhang-bear_body.md`

part_bear_body.step.py: 159.4 cm2 of surface, grid 0.400 mm, 943 unsupported samples over 6 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 25.8% of the surface faces down that steeply; 0 region(s) need support, 6 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 6 region(s), longest span 6.9 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 36.0 | (25.2, -31.2, 1.3) | 6.5 | 2.4 |
| 2 | bridge | 35.5 | (-24.8, -31.2, 1.3) | 6.9 | 2.8 |
| 3 | bridge | 23.5 | (0.1, 30.7, 27.2) | 2.7 | 20.0 |
| 4 | bridge | 19.4 | (-24.9, -31.2, 20.6) | 2.5 | 6.4 |
| 5 | bridge | 19.4 | (25.2, -31.5, 20.6) | 2.5 | 6.4 |
| 6 | bridge | 4.9 | (-10.8, -2.9, 1.3) | 0.8 | 2.4 |

RESULT: prints unsupported

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
