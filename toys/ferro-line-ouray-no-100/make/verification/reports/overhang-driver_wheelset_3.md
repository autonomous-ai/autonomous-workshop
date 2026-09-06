# Overhang and support

`artifacts/make/r0001/product/cad-project/part_driver_wheelset_3.stl --angle 45.0 --report artifacts/make/r0001/product/cad-project/measure/overhang-driver_wheelset_3.md`

artifacts/make/r0001/product/cad-project/part_driver_wheelset_3.stl: 8.3 cm2 of surface, grid 0.400 mm, 933 unsupported samples over 1 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 16.3% of the surface faces down that steeply; 0 region(s) need support, 1 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 1 region(s), longest span 8.6 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 112.9 | (62.8, -0.0, 4.1) | 8.6 | 10.0 |

Measured on the exported STL, in the pose it is printed in. The fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
