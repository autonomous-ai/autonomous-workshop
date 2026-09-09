# Overhang and support

`artifacts/make/r0001/product/cybercab/part_chassis.stl --angle 45.0 --report artifacts/make/r0001/product/cybercab/measure/overhang-chassis.md`

artifacts/make/r0001/product/cybercab/part_chassis.stl: 213.0 cm2 of surface, grid 0.400 mm, 516 unsupported samples over 5 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 37.2% of the surface faces down that steeply; 0 region(s) need support, 5 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 5 region(s), longest span 8.7 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 30.0 | (133.8, -0.2, 6.3) | 8.7 | 3.6 |
| 2 | bridge | 11.0 | (71.0, -20.0, 13.8) | 2.4 | 10.8 |
| 3 | bridge | 11.0 | (71.0, 19.9, 13.8) | 2.4 | 10.8 |
| 4 | bridge | 11.0 | (108.0, -19.9, 13.8) | 2.3 | 10.8 |
| 5 | bridge | 10.9 | (108.1, 20.1, 13.8) | 2.4 | 14.8 |

Measured on the exported STL, in the pose it is printed in. The fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
