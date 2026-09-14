# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_camera_board.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/camera_board/r0006/overhang-camera_board.md`

part_camera_board.step.py: 987.1 cm2 of surface, grid 0.463 mm, 24 unsupported samples over 3 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 36.7% of the surface faces down that steeply; 0 region(s) need support, 3 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 3 region(s), longest span 0.8 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 2.0 | (87.6, 5.3, 25.0) | 0.8 | 3.2 |
| 2 | bridge | 1.6 | (87.5, 45.4, 25.0) | 0.8 | 3.2 |
| 3 | bridge | 1.2 | (87.5, -35.0, 25.0) | 0.6 | 3.2 |

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
