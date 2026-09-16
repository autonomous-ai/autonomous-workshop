# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_piece.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/piece/r0008/overhang-piece.md`

part_piece.step.py: 36.1 cm2 of surface, grid 0.400 mm, 22 unsupported samples over 7 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 25.2% of the surface faces down that steeply; 0 region(s) need support, 0 bridge, 7 below 1 mm2 |
| bridges within 12 mm | PASS | 0 region(s), longest span 0.0 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | trace | 0.7 | (8.9, 5.8, 16.9) | 0.8 | 11.6 |
| 2 | trace | 0.4 | (-10.2, -1.5, 17.5) | 0.1 | 12.8 |
| 3 | trace | 0.4 | (6.3, -6.9, 7.5) | 0.4 | 2.8 |
| 4 | trace | 0.3 | (1.2, 8.3, 7.1) | 0.1 | 2.0 |
| 5 | trace | 0.3 | (2.4, -8.3, 19.9) | 0.1 | 0.8 |
| 6 | trace | 0.3 | (5.7, 6.8, 7.6) | 0.2 | 2.8 |
| 7 | trace | 0.0 | (-8.1, -7.9, 15.7) | 0.2 | 10.8 |

RESULT: prints unsupported

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
