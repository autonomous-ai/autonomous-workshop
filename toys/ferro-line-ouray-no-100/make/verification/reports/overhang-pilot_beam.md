# Overhang and support

`artifacts/make/r0001/product/cad-project/part_pilot_beam.stl --angle 45.0 --report artifacts/make/r0001/product/cad-project/measure/overhang-pilot_beam.md`

artifacts/make/r0001/product/cad-project/part_pilot_beam.stl: 23.5 cm2 of surface, grid 0.400 mm, 892 unsupported samples over 2 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 6.0% of the surface faces down that steeply; 0 region(s) need support, 2 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 2 region(s), longest span 8.7 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 100.7 | (-9.4, -7.7, 15.6) | 8.7 | 20.4 |
| 2 | bridge | 36.7 | (0.9, -7.4, 7.6) | 6.9 | 12.4 |

Measured on the exported STL, in the pose it is printed in. The fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
