# Overhang and support

`artifacts/make/r0001/product/cad-project/part_tender_wheelset_1.stl --angle 45.0 --report artifacts/make/r0001/product/cad-project/measure/overhang-tender_wheelset_1.md`

artifacts/make/r0001/product/cad-project/part_tender_wheelset_1.stl: 5.4 cm2 of surface, grid 0.400 mm, 583 unsupported samples over 4 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 16.7% of the surface faces down that steeply; 0 region(s) need support, 1 bridge, 3 below 1 mm2 |
| bridges within 12 mm | PASS | 1 region(s), longest span 5.8 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 68.3 | (123.9, -0.1, 2.1) | 5.8 | 4.4 |
| 2 | trace | 0.3 | (123.4, 5.5, 6.3) | 0.1 | 1.2 |
| 3 | trace | 0.2 | (124.0, -6.2, 6.3) | 0.1 | 1.2 |
| 4 | trace | 0.1 | (123.3, -4.5, 6.3) | 0.0 | 0.8 |

Measured on the exported STL, in the pose it is printed in. The fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
