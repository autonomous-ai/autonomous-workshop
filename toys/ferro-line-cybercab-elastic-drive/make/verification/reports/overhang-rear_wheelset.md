# Overhang and support

`artifacts/make/r0001/product/cybercab/part_rear_wheelset.stl --angle 45.0 --report artifacts/make/r0001/product/cybercab/measure/overhang-rear_wheelset.md`

artifacts/make/r0001/product/cybercab/part_rear_wheelset.stl: 38.4 cm2 of surface, grid 0.400 mm, 109 unsupported samples over 1 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 22.6% of the surface faces down that steeply; 0 region(s) need support, 1 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 1 region(s), longest span 7.9 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 13.2 | (1.8, 0.0, 34.0) | 7.9 | 20.0 |

Measured on the exported STL, in the pose it is printed in. The fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
