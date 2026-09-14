# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_deck_0_1.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0004/overhang-deck_0_1.md`

part_deck_0_1.step.py: 643.4 cm2 of surface, grid 0.400 mm, 7386 unsupported samples over 4 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | FAIL | 38.6% of the surface faces down that steeply; 1 region(s) need support, 3 bridge, 0 below 1 mm2; worst 220.6 mm2 spanning 6.9 mm |
| bridges within 12 mm | PASS | 3 region(s), longest span 10.2 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 326.8 | (144.0, 41.1, 1.2) | 10.2 | 2.4 |
| 2 | bridge | 320.1 | (144.2, 14.9, 1.2) | 10.0 | 2.4 |
| 3 | bridge | 313.8 | (143.8, 28.2, 1.2) | 9.8 | 2.4 |
| 4 | overhang | 220.6 | (144.0, 3.5, 1.2) | 6.9 | 2.4 |

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
