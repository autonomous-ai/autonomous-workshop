# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/part_carrier.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/measure/rounds/r0001/overhang-carrier.md`

part_carrier.step.py: 117.3 cm2 of surface, grid 0.400 mm, 170 unsupported samples over 16 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 27.5% of the surface faces down that steeply; 0 region(s) need support, 1 bridge, 15 below 1 mm2 |
| bridges within 12 mm | PASS | 1 region(s), longest span 5.5 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 1.1 | (-71.8, 17.9, 3.0) | 5.5 | 4.0 |
| 2 | trace | 0.3 | (-42.1, 1.4, 3.0) | 1.4 | 4.0 |
| 3 | trace | 0.2 | (40.9, -2.5, 3.0) | 3.6 | 4.0 |
| 4 | trace | 0.1 | (68.4, -17.1, 3.0) | 1.5 | 4.0 |
| 5 | trace | 0.1 | (-20.4, -50.3, 3.0) | 0.6 | 4.0 |
| 6 | trace | 0.1 | (11.7, -60.0, 3.0) | 0.1 | 4.0 |
| 7 | trace | 0.1 | (-39.9, -26.7, 3.0) | 0.5 | 4.0 |
| 8 | trace | 0.1 | (46.8, -50.2, 3.0) | 0.7 | 4.0 |

RESULT: prints unsupported

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
