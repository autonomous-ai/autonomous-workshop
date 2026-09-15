# Overhang and support

`part_access_receiver_load.step.py --angle 45.0 --report measure/overhang-access_receiver_load.md`

part_access_receiver_load.step.py: 351.3 cm2 of surface, grid 0.441 mm, 2192 unsupported samples over 10 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 21.8% of the surface faces down that steeply; 0 region(s) need support, 10 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 10 region(s), longest span 7.5 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 84.8 | (182.9, 111.9, 17.3) | 7.5 | 19.8 |
| 2 | bridge | 83.4 | (183.1, 32.0, 17.2) | 7.5 | 19.8 |
| 3 | bridge | 72.6 | (9.7, 29.9, 10.0) | 7.2 | 4.9 |
| 4 | bridge | 70.4 | (9.6, 114.1, 10.0) | 7.0 | 4.9 |
| 5 | bridge | 17.9 | (170.0, 24.1, 24.0) | 3.2 | 20.0 |
| 6 | bridge | 17.9 | (170.0, 39.8, 24.0) | 3.2 | 20.0 |
| 7 | bridge | 17.9 | (169.9, 104.2, 24.0) | 3.2 | 20.0 |
| 8 | bridge | 17.9 | (170.0, 119.7, 24.0) | 3.1 | 4.4 |

RESULT: prints unsupported

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
