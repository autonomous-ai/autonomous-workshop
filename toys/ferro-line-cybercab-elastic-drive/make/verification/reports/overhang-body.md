# Overhang and support

`artifacts/make/r0001/product/cybercab/part_body.stl --angle 45.0 --report artifacts/make/r0001/product/cybercab/measure/overhang-body.md`

artifacts/make/r0001/product/cybercab/part_body.stl: 639.3 cm2 of surface, grid 0.420 mm, 2225 unsupported samples over 17 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 1.2% of the surface faces down that steeply; 0 region(s) need support, 17 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 17 region(s), longest span 6.0 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 63.6 | (34.0, -31.4, 106.6) | 6.0 | 20.0 |
| 2 | bridge | 63.6 | (34.0, 31.5, 106.6) | 6.0 | 20.0 |
| 3 | bridge | 63.4 | (34.0, 31.2, 69.6) | 6.0 | 20.0 |
| 4 | bridge | 63.2 | (34.0, -31.3, 69.6) | 6.0 | 20.0 |
| 5 | bridge | 21.8 | (24.1, -20.1, 73.5) | 2.9 | 20.0 |
| 6 | bridge | 21.6 | (23.9, 20.2, 110.5) | 2.9 | 20.0 |
| 7 | bridge | 21.2 | (24.0, -19.8, 110.5) | 2.9 | 20.0 |
| 8 | bridge | 21.2 | (24.1, 20.0, 73.5) | 2.9 | 20.0 |

Measured on the exported STL, in the pose it is printed in. The fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
