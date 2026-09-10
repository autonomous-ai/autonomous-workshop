# Overhang and support

`artifacts/make/r0001/product/cad/part_bishop.stl --angle 45.0 --report artifacts/make/r0001/product/cad/measure/overhang-bishop.md`

artifacts/make/r0001/product/cad/part_bishop.stl: 59.2 cm2 of surface, grid 0.400 mm, 51 unsupported samples over 7 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 10.9% of the surface faces down that steeply; 0 region(s) need support, 3 bridge, 4 below 1 mm2 |
| bridges within 12 mm | PASS | 3 region(s), longest span 2.4 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 1.8 | (-5.4, -2.6, 51.0) | 2.4 | 20.0 |
| 2 | bridge | 1.2 | (3.9, -6.1, 51.0) | 2.2 | 20.0 |
| 3 | bridge | 1.2 | (1.7, -2.1, 62.9) | 0.5 | 4.4 |
| 4 | trace | 0.9 | (-8.0, 3.4, 51.0) | 0.6 | 20.0 |
| 5 | trace | 0.9 | (6.7, 0.4, 51.0) | 0.4 | 20.0 |
| 6 | trace | 0.9 | (-2.8, -8.4, 51.0) | 0.7 | 20.0 |
| 7 | trace | 0.8 | (8.5, 4.2, 51.0) | 0.5 | 20.0 |

Measured on the exported STL, in the pose it is printed in. The fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
