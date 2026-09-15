# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_deck_1_1.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0004/overhang-deck_1_1.md`

part_deck_1_1.step.py: 695.6 cm2 of surface, grid 0.400 mm, 38 unsupported samples over 7 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | FAIL | 35.8% of the surface faces down that steeply; 2 region(s) need support, 0 bridge, 5 below 1 mm2; worst 1.5 mm2 spanning 0.1 mm |
| bridges within 12 mm | PASS | 0 region(s), longest span 0.0 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | overhang | 1.5 | (0.2, 42.4, 1.2) | 0.1 | 2.4 |
| 2 | overhang | 1.3 | (0.2, 13.9, 1.2) | 0.1 | 2.4 |
| 3 | trace | 0.9 | (0.2, 1.3, 1.2) | 0.1 | 2.4 |
| 4 | trace | 0.9 | (0.2, 30.3, 1.2) | 0.1 | 2.4 |
| 5 | trace | 0.6 | (0.2, 24.7, 1.2) | 0.0 | 2.4 |
| 6 | trace | 0.1 | (0.2, 19.9, 1.2) | 0.0 | 2.4 |
| 7 | trace | 0.1 | (0.2, 5.4, 1.2) | 0.0 | 2.4 |

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
