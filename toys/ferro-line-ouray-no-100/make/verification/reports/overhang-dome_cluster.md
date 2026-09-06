# Overhang and support

`artifacts/make/r0001/product/cad-project/part_dome_cluster.stl --angle 45.0 --report artifacts/make/r0001/product/cad-project/measure/overhang-dome_cluster.md`

artifacts/make/r0001/product/cad-project/part_dome_cluster.stl: 9.7 cm2 of surface, grid 0.400 mm, 996 unsupported samples over 2 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 17.4% of the surface faces down that steeply; 0 region(s) need support, 2 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 2 region(s), longest span 9.7 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 87.1 | (52.0, -40.0, 1.6) | 9.7 | 5.2 |
| 2 | bridge | 53.7 | (64.9, -40.7, 0.9) | 7.8 | 2.8 |

Measured on the exported STL, in the pose it is printed in. The fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
