# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_deck_1_2.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0004/overhang-deck_1_2.md`

part_deck_1_2.step.py: 710.6 cm2 of surface, grid 0.400 mm, 959 unsupported samples over 2 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | FAIL | 35.1% of the surface faces down that steeply; 2 region(s) need support, 0 bridge, 0 below 1 mm2; worst 77.3 mm2 spanning 7.0 mm |
| bridges within 12 mm | PASS | 0 region(s), longest span 0.0 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | overhang | 77.3 | (6.7, 137.8, 1.2) | 7.0 | 2.4 |
| 2 | overhang | 66.0 | (6.3, 146.8, 1.2) | 9.0 | 2.4 |

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
