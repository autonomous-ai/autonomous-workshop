# Overhang and support

`artifacts/make/r0001/product/cad/part_frame.stl --angle 45.0 --report artifacts/make/r0001/product/cad/measure/overhang-frame.md`

artifacts/make/r0001/product/cad/part_frame.stl: 352.0 cm2 of surface, grid 0.400 mm, 209 unsupported samples over 5 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 23.4% of the surface faces down that steeply; 0 region(s) need support, 4 bridge, 1 below 1 mm2 |
| bridges within 12 mm | PASS | 4 region(s), longest span 2.5 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 11.2 | (-26.7, 6.0, 7.5) | 2.5 | 3.2 |
| 2 | bridge | 11.2 | (26.6, 6.0, 7.5) | 2.4 | 3.2 |
| 3 | bridge | 2.7 | (22.3, 69.0, 13.0) | 0.6 | 14.0 |
| 4 | bridge | 1.6 | (-40.0, 20.6, 26.1) | 0.8 | 5.2 |
| 5 | trace | 0.4 | (-23.7, 17.5, 19.0) | 0.0 | 6.0 |

Measured on the exported STL, in the pose it is printed in. The fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
