# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_return_hood_3.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0009/overhang-return_hood_3.md`

part_return_hood_3.step.py: 275.0 cm2 of surface, grid 0.400 mm, 1811 unsupported samples over 4 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 17.5% of the surface faces down that steeply; 0 region(s) need support, 4 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 4 region(s), longest span 11.5 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 94.5 | (16.1, 25.0, 2.5) | 11.5 | 3.6 |
| 2 | bridge | 94.2 | (139.1, 74.0, 2.5) | 11.5 | 3.6 |
| 3 | bridge | 30.0 | (9.4, 37.2, 16.0) | 7.3 | 17.2 |
| 4 | bridge | 28.6 | (96.1, 39.2, 16.0) | 7.2 | 17.2 |

RESULT: prints unsupported

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
