# Overhang and support

`artifacts/make/r0001/product/cad-project/part_driver_wheelset_4.stl --angle 45.0 --report artifacts/make/r0001/product/cad-project/measure/overhang-driver_wheelset_4.md`

artifacts/make/r0001/product/cad-project/part_driver_wheelset_4.stl: 8.3 cm2 of surface, grid 0.400 mm, 987 unsupported samples over 3 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 17.5% of the surface faces down that steeply; 0 region(s) need support, 3 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 3 region(s), longest span 8.8 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 107.3 | (73.9, -0.0, 3.2) | 8.8 | 5.6 |
| 2 | bridge | 6.8 | (74.1, 5.2, 9.0) | 2.2 | 10.0 |
| 3 | bridge | 6.5 | (74.2, -5.3, 8.9) | 2.1 | 2.4 |

Measured on the exported STL, in the pose it is printed in. The fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
