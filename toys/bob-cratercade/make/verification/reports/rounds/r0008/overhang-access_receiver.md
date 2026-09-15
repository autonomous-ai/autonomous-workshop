# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_access_receiver.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0008/overhang-access_receiver.md`

part_access_receiver.step.py: 351.8 cm2 of surface, grid 0.441 mm, 2182 unsupported samples over 9 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 21.8% of the surface faces down that steeply; 0 region(s) need support, 9 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 9 region(s), longest span 7.5 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 84.8 | (4.7, 111.7, 17.2) | 7.5 | 19.8 |
| 2 | bridge | 84.2 | (4.8, 32.1, 17.2) | 7.5 | 19.8 |
| 3 | bridge | 71.6 | (178.3, 29.9, 10.0) | 7.2 | 4.9 |
| 4 | bridge | 68.8 | (178.3, 114.2, 10.0) | 7.0 | 4.9 |
| 5 | bridge | 24.4 | (18.0, 121.9, 24.0) | 3.2 | 6.2 |
| 6 | bridge | 17.9 | (17.9, 23.9, 24.0) | 3.2 | 20.0 |
| 7 | bridge | 17.9 | (18.0, 39.7, 24.0) | 3.2 | 20.0 |
| 8 | bridge | 17.9 | (18.0, 104.3, 24.0) | 3.1 | 20.0 |

RESULT: prints unsupported

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
