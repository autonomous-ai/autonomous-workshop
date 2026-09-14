# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_deck_0_2.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0004/overhang-deck_0_2.md`

part_deck_0_2.step.py: 627.6 cm2 of surface, grid 0.400 mm, 3374 unsupported samples over 2 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 38.2% of the surface faces down that steeply; 0 region(s) need support, 2 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 2 region(s), longest span 10.0 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 374.2 | (139.7, 148.7, 1.2) | 10.0 | 2.4 |
| 2 | bridge | 155.3 | (132.6, 138.7, 1.2) | 7.1 | 2.4 |

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
