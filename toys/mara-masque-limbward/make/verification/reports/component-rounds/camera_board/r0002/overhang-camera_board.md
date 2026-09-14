# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_camera_board.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/camera_board/r0002/overhang-camera_board.md`

part_camera_board.step.py: 973.2 cm2 of surface, grid 0.463 mm, 432 unsupported samples over 1 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | FAIL | 37.0% of the surface faces down that steeply; 1 region(s) need support, 0 bridge, 0 below 1 mm2; worst 90.7 mm2 spanning 2.0 mm |
| bridges within 12 mm | PASS | 0 region(s), longest span 0.0 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | overhang | 90.7 | (-0.0, -97.1, 17.9) | 2.0 | 20.4 |

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
