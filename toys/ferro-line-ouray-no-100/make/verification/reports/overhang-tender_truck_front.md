# Overhang and support

`artifacts/make/r0001/product/cad-project/part_tender_truck_front.stl --angle 45.0 --report artifacts/make/r0001/product/cad-project/measure/overhang-tender_truck_front.md`

artifacts/make/r0001/product/cad-project/part_tender_truck_front.stl: 18.4 cm2 of surface, grid 0.400 mm, 373 unsupported samples over 2 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 9.0% of the surface faces down that steeply; 0 region(s) need support, 2 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 2 region(s), longest span 4.8 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 48.4 | (129.9, -4.4, 17.0) | 4.8 | 18.0 |
| 2 | bridge | 3.3 | (130.0, -1.4, 12.0) | 1.2 | 8.0 |

Measured on the exported STL, in the pose it is printed in. The fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
