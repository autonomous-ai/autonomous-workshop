# Overhang and support

`artifacts/make/r0001/product/cad-project/part_boiler_smokebox.stl --angle 45.0 --report artifacts/make/r0001/product/cad-project/measure/overhang-boiler_smokebox.md`

artifacts/make/r0001/product/cad-project/part_boiler_smokebox.stl: 94.8 cm2 of surface, grid 0.400 mm, 100 unsupported samples over 14 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 6.8% of the surface faces down that steeply; 0 region(s) need support, 3 bridge, 11 below 1 mm2 |
| bridges within 12 mm | PASS | 3 region(s), longest span 5.8 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 3.0 | (26.4, -11.3, 60.0) | 5.8 | 20.0 |
| 2 | bridge | 1.1 | (11.6, -0.1, 60.0) | 0.4 | 20.0 |
| 3 | bridge | 1.1 | (15.4, -9.1, 60.0) | 3.6 | 20.0 |
| 4 | trace | 0.8 | (11.2, -6.0, 19.5) | 0.3 | 20.0 |
| 5 | trace | 0.8 | (11.2, 6.0, 19.5) | 0.3 | 20.0 |
| 6 | trace | 0.8 | (36.7, -6.0, 19.5) | 0.3 | 20.0 |
| 7 | trace | 0.8 | (11.2, 0.1, 19.5) | 0.4 | 20.0 |
| 8 | trace | 0.7 | (15.5, 9.2, 60.0) | 3.0 | 20.0 |

Measured on the exported STL, in the pose it is printed in. The fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
