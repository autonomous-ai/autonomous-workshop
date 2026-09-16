# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_frame.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/frame/r0002/overhang-frame.md`

part_frame.step.py: 113.2 cm2 of surface, grid 0.400 mm, 45 unsupported samples over 2 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | FAIL | 19.7% of the surface faces down that steeply; 2 region(s) need support, 0 bridge, 0 below 1 mm2; worst 3.0 mm2 spanning 1.5 mm |
| bridges within 12 mm | PASS | 0 region(s), longest span 0.0 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | overhang | 3.0 | (-2.9, 26.4, 3.0) | 1.5 | 4.0 |
| 2 | overhang | 2.9 | (-20.7, -16.5, 3.0) | 1.6 | 4.0 |

RESULT: NEEDS SUPPORT

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
