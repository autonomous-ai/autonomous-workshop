# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_piece.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/piece/r0002/overhang-piece.md`

part_piece.step.py: 36.7 cm2 of surface, grid 0.400 mm, 34 unsupported samples over 9 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 24.8% of the surface faces down that steeply; 0 region(s) need support, 1 bridge, 8 below 1 mm2 |
| bridges within 12 mm | PASS | 1 region(s), longest span 0.9 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 1.0 | (9.1, 5.7, 18.0) | 0.9 | 12.4 |
| 2 | trace | 0.8 | (-5.3, -6.5, 7.3) | 1.2 | 2.8 |
| 3 | trace | 0.7 | (9.5, -2.3, 20.0) | 0.4 | 2.0 |
| 4 | trace | 0.5 | (1.2, 8.6, 7.7) | 0.7 | 3.2 |
| 5 | trace | 0.3 | (-9.8, -4.3, 16.6) | 0.1 | 12.4 |
| 6 | trace | 0.3 | (2.4, -8.7, 20.9) | 0.0 | 1.2 |
| 7 | trace | 0.3 | (5.7, 7.0, 8.2) | 0.1 | 3.6 |
| 8 | trace | 0.1 | (6.9, -4.9, 22.0) | 0.0 | 1.2 |

RESULT: prints unsupported

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
