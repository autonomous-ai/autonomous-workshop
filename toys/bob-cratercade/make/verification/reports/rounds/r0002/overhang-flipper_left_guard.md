# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_flipper_left_guard.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0002/overhang-flipper_left_guard.md`

part_flipper_left_guard.step.py: 130.9 cm2 of surface, grid 0.400 mm, 311 unsupported samples over 4 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | FAIL | 26.7% of the surface faces down that steeply; 3 region(s) need support, 0 bridge, 1 below 1 mm2; worst 19.4 mm2 spanning 3.2 mm |
| bridges within 12 mm | PASS | 0 region(s), longest span 0.0 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | overhang | 19.4 | (-60.9, 47.9, 3.0) | 3.2 | 4.0 |
| 2 | overhang | 15.5 | (48.2, 26.1, 3.0) | 2.4 | 4.0 |
| 3 | overhang | 8.5 | (-61.0, 7.4, 3.0) | 1.4 | 4.0 |
| 4 | trace | 0.4 | (42.7, 32.4, 3.0) | 0.2 | 4.0 |

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
