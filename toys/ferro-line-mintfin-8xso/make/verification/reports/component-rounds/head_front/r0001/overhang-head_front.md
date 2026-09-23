# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_head_front.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/head_front/r0001/overhang-head_front.md`

part_head_front.step.py: 97.0 cm2 of surface, grid 0.400 mm, 2117 unsupported samples over 1 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | FAIL | 28.4% of the surface faces down that steeply; 1 region(s) need support, 0 bridge, 0 below 1 mm2; worst 327.0 mm2 spanning 39.3 mm |
| bridges within 12 mm | PASS | 0 region(s), longest span 0.0 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | overhang | 327.0 | (-0.9, -6.4, 21.2) | 39.3 | 20.0 |

RESULT: NEEDS SUPPORT

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
