# Overhang and support

`artifacts/make/r0001/product/cad-project/part_headlamp.stl --angle 45.0 --report artifacts/make/r0001/product/cad-project/measure/overhang-headlamp.md`

artifacts/make/r0001/product/cad-project/part_headlamp.stl: 10.8 cm2 of surface, grid 0.400 mm, 142 unsupported samples over 6 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 17.5% of the surface faces down that steeply; 0 region(s) need support, 2 bridge, 4 below 1 mm2 |
| bridges within 12 mm | PASS | 2 region(s), longest span 11.0 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 16.1 | (20.3, -3.4, 2.4) | 11.0 | 4.0 |
| 2 | bridge | 1.8 | (18.3, -6.5, 6.2) | 1.8 | 7.2 |
| 3 | trace | 0.9 | (17.8, 0.0, 7.4) | 0.4 | 8.4 |
| 4 | trace | 0.9 | (17.6, 4.3, 7.4) | 0.5 | 8.4 |
| 5 | trace | 0.7 | (23.8, -7.3, 7.4) | 0.3 | 8.4 |
| 6 | trace | 0.5 | (27.6, -7.4, 7.4) | 0.4 | 8.4 |

Measured on the exported STL, in the pose it is printed in. The fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
