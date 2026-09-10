# Overhang and support

`artifacts/make/r0001/product/cad/part_king.stl --angle 45.0 --report artifacts/make/r0001/product/cad/measure/overhang-king.md`

artifacts/make/r0001/product/cad/part_king.stl: 70.2 cm2 of surface, grid 0.400 mm, 45 unsupported samples over 12 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 10.5% of the surface faces down that steeply; 0 region(s) need support, 0 bridge, 12 below 1 mm2 |
| bridges within 12 mm | PASS | 0 region(s), longest span 0.0 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | trace | 0.8 | (-3.9, -8.1, 33.0) | 0.4 | 6.0 |
| 2 | trace | 0.8 | (-4.0, -6.7, 60.0) | 0.5 | 20.0 |
| 3 | trace | 0.8 | (0.0, 8.2, 33.0) | 0.5 | 6.0 |
| 4 | trace | 0.7 | (0.3, -8.2, 33.0) | 0.6 | 6.8 |
| 5 | trace | 0.7 | (0.3, -6.6, 60.0) | 0.5 | 20.0 |
| 6 | trace | 0.6 | (4.3, -8.1, 33.0) | 0.4 | 6.0 |
| 7 | trace | 0.4 | (-3.6, 8.2, 33.0) | 0.4 | 6.0 |
| 8 | trace | 0.4 | (4.6, -6.6, 60.0) | 0.1 | 20.0 |

Measured on the exported STL, in the pose it is printed in. The fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
