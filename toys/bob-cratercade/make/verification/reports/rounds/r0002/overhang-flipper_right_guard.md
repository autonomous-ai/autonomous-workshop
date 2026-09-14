# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_flipper_right_guard.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0002/overhang-flipper_right_guard.md`

part_flipper_right_guard.step.py: 84.0 cm2 of surface, grid 0.400 mm, 229 unsupported samples over 3 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | FAIL | 27.1% of the surface faces down that steeply; 2 region(s) need support, 0 bridge, 1 below 1 mm2; worst 15.8 mm2 spanning 2.3 mm |
| bridges within 12 mm | PASS | 0 region(s), longest span 0.0 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | overhang | 15.8 | (-48.2, 26.0, 3.0) | 2.3 | 4.0 |
| 2 | overhang | 15.8 | (21.5, 6.9, 3.0) | 2.3 | 4.0 |
| 3 | trace | 0.2 | (-43.3, 32.4, 3.0) | 0.0 | 4.0 |

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
