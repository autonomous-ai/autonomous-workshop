# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_bull_body.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/overhang-bull_body.md`

part_bull_body.step.py: 160.7 cm2 of surface, grid 0.400 mm, 595 unsupported samples over 7 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 24.9% of the surface faces down that steeply; 0 region(s) need support, 5 bridge, 2 below 1 mm2 |
| bridges within 12 mm | PASS | 5 region(s), longest span 3.4 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 21.7 | (0.2, 29.4, 27.2) | 2.7 | 20.0 |
| 2 | bridge | 21.0 | (27.0, -25.5, 20.6) | 2.6 | 20.0 |
| 3 | bridge | 21.0 | (-26.9, -25.7, 20.6) | 2.7 | 20.0 |
| 4 | bridge | 13.0 | (-4.9, -23.3, 1.3) | 2.9 | 2.4 |
| 5 | bridge | 12.6 | (19.0, -23.4, 1.3) | 3.4 | 2.4 |
| 6 | trace | 0.2 | (27.0, -29.4, 4.0) | 0.1 | 5.2 |
| 7 | trace | 0.2 | (-26.9, -29.4, 4.0) | 0.1 | 5.2 |

RESULT: prints unsupported

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
