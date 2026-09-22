# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_head.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/head/r0001/overhang-head.md`

part_head.step.py: 61.2 cm2 of surface, grid 0.400 mm, 362 unsupported samples over 3 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | FAIL | 20.9% of the surface faces down that steeply; 1 region(s) need support, 2 bridge, 0 below 1 mm2; worst 17.0 mm2 spanning 5.6 mm |
| bridges within 12 mm | PASS | 2 region(s), longest span 8.1 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 18.6 | (33.8, -0.0, 6.5) | 8.1 | 8.0 |
| 2 | overhang | 17.0 | (19.3, 13.7, 20.0) | 5.6 | 2.8 |
| 3 | bridge | 7.2 | (23.1, -12.8, 19.9) | 4.8 | 2.4 |

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
