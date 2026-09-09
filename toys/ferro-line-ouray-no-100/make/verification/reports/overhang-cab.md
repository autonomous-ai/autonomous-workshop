# Overhang and support

`artifacts/make/r0001/product/cad-project/part_cab.stl --angle 45.0 --report artifacts/make/r0001/product/cad-project/measure/overhang-cab.md`

artifacts/make/r0001/product/cad-project/part_cab.stl: 80.7 cm2 of surface, grid 0.400 mm, 547 unsupported samples over 4 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 12.2% of the surface faces down that steeply; 0 region(s) need support, 4 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 4 region(s), longest span 2.5 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 23.8 | (81.0, 13.5, 23.0) | 2.0 | 14.8 |
| 2 | bridge | 23.7 | (80.8, -13.4, 23.0) | 2.0 | 20.0 |
| 3 | bridge | 20.0 | (95.7, -5.6, 23.0) | 2.5 | 14.8 |
| 4 | bridge | 19.7 | (95.7, 6.0, 23.0) | 2.5 | 14.8 |

Measured on the exported STL, in the pose it is printed in. The fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
