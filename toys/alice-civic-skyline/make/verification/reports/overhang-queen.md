# Overhang and support

`artifacts/make/r0001/product/cad/part_queen.stl --angle 45.0 --report artifacts/make/r0001/product/cad/measure/overhang-queen.md`

artifacts/make/r0001/product/cad/part_queen.stl: 64.7 cm2 of surface, grid 0.400 mm, 102 unsupported samples over 15 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 11.6% of the surface faces down that steeply; 0 region(s) need support, 3 bridge, 12 below 1 mm2 |
| bridges within 12 mm | PASS | 3 region(s), longest span 0.6 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 3.3 | (-4.0, -6.7, 56.0) | 0.6 | 7.2 |
| 2 | bridge | 3.3 | (4.2, -6.7, 56.0) | 0.6 | 6.8 |
| 3 | bridge | 1.3 | (-4.4, 6.9, 55.7) | 0.2 | 2.4 |
| 4 | trace | 0.9 | (3.3, -5.2, 61.4) | 0.5 | 1.2 |
| 5 | trace | 0.7 | (-3.8, -8.1, 44.0) | 0.5 | 20.0 |
| 6 | trace | 0.7 | (4.1, -8.2, 44.0) | 0.4 | 20.0 |
| 7 | trace | 0.7 | (3.9, 8.1, 44.0) | 0.4 | 20.0 |
| 8 | trace | 0.7 | (0.1, -8.2, 44.0) | 0.6 | 20.0 |

Measured on the exported STL, in the pose it is printed in. The fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
