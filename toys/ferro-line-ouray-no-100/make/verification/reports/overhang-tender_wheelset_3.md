# Overhang and support

`artifacts/make/r0001/product/cad-project/part_tender_wheelset_3.stl --angle 45.0 --report artifacts/make/r0001/product/cad-project/measure/overhang-tender_wheelset_3.md`

artifacts/make/r0001/product/cad-project/part_tender_wheelset_3.stl: 5.4 cm2 of surface, grid 0.400 mm, 594 unsupported samples over 5 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 16.9% of the surface faces down that steeply; 0 region(s) need support, 1 bridge, 4 below 1 mm2 |
| bridges within 12 mm | PASS | 1 region(s), longest span 5.7 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 67.7 | (150.9, -0.1, 2.1) | 5.7 | 4.4 |
| 2 | trace | 0.7 | (150.8, -6.1, 5.8) | 0.6 | 6.4 |
| 3 | trace | 0.2 | (149.1, 5.0, 5.5) | 1.8 | 6.4 |
| 4 | trace | 0.2 | (153.3, 5.2, 5.3) | 0.3 | 6.4 |
| 5 | trace | 0.1 | (153.4, -4.2, 5.3) | 0.1 | 0.8 |

Measured on the exported STL, in the pose it is printed in. The fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
