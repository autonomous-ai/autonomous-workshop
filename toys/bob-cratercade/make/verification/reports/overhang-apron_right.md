# Overhang and support

`part_apron_right.step.py --angle 45.0 --report measure/overhang-apron_right.md`

part_apron_right.step.py: 225.9 cm2 of surface, grid 0.400 mm, 1010 unsupported samples over 25 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 26.0% of the surface faces down that steeply; 0 region(s) need support, 3 bridge, 22 below 1 mm2 |
| bridges within 12 mm | PASS | 3 region(s), longest span 9.7 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 125.3 | (234.4, -40.4, 1.5) | 0.9 | 2.8 |
| 2 | bridge | 7.5 | (171.1, -9.2, 22.5) | 9.7 | 20.0 |
| 3 | bridge | 7.3 | (175.0, -46.0, 22.5) | 9.5 | 20.0 |
| 4 | trace | 0.3 | (167.1, -64.0, 3.0) | 0.0 | 4.0 |
| 5 | trace | 0.3 | (204.2, -64.0, 3.0) | 0.0 | 4.0 |
| 6 | trace | 0.2 | (187.9, -64.0, 3.0) | 0.0 | 4.0 |
| 7 | trace | 0.2 | (216.1, -64.0, 3.0) | 0.0 | 4.0 |
| 8 | trace | 0.2 | (244.5, -64.0, 3.0) | 0.0 | 4.0 |

RESULT: prints unsupported

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
