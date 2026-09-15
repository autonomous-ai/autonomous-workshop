# Overhang and support

`part_deck_0_1.step.py --angle 45.0 --report measure/overhang-deck_0_1.md`

part_deck_0_1.step.py: 644.2 cm2 of surface, grid 0.400 mm, 6741 unsupported samples over 4 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 38.6% of the surface faces down that steeply; 0 region(s) need support, 4 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 4 region(s), longest span 10.2 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 327.0 | (144.0, 41.1, 1.2) | 10.2 | 2.4 |
| 2 | bridge | 318.6 | (144.1, 14.9, 1.2) | 10.0 | 2.4 |
| 3 | bridge | 312.2 | (144.0, 28.2, 1.2) | 9.8 | 2.4 |
| 4 | bridge | 120.4 | (144.1, 5.1, 1.2) | 3.8 | 2.4 |

RESULT: prints unsupported

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
