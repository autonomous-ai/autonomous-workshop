# Overhang and support

`artifacts/make/r0001/product/cad-project/part_locomotive_frame.stl --angle 45.0 --report artifacts/make/r0001/product/cad-project/measure/overhang-locomotive_frame.md`

artifacts/make/r0001/product/cad-project/part_locomotive_frame.stl: 27.6 cm2 of surface, grid 0.400 mm, 1234 unsupported samples over 6 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 25.2% of the surface faces down that steeply; 0 region(s) need support, 6 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 6 region(s), longest span 4.0 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 85.4 | (105.4, -0.1, 4.0) | 4.0 | 5.2 |
| 2 | bridge | 21.4 | (41.0, 0.1, 3.3) | 2.4 | 4.4 |
| 3 | bridge | 21.4 | (52.0, -0.4, 3.3) | 2.4 | 4.4 |
| 4 | bridge | 21.4 | (74.0, -0.2, 3.3) | 2.4 | 4.4 |
| 5 | bridge | 20.8 | (63.0, -0.0, 3.3) | 2.4 | 4.4 |
| 6 | bridge | 7.5 | (119.0, -0.1, 4.6) | 1.6 | 6.0 |

Measured on the exported STL, in the pose it is printed in. The fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
