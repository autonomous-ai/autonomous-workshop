# Overhang and support

`part_canopy_post_rear_right.step.py --angle 45.0 --report measure/overhang-canopy_post_rear_right.md`

part_canopy_post_rear_right.step.py: 110.3 cm2 of surface, grid 0.400 mm, 910 unsupported samples over 4 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 2.9% of the surface faces down that steeply; 0 region(s) need support, 4 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 4 region(s), longest span 7.8 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 76.6 | (-4.7, 0.2, 79.0) | 7.8 | 20.0 |
| 2 | bridge | 26.3 | (-5.0, 0.0, 93.0) | 3.2 | 8.4 |
| 3 | bridge | 20.5 | (-10.7, -0.1, 9.0) | 3.0 | 11.2 |
| 4 | bridge | 10.3 | (0.6, -0.0, 8.6) | 3.2 | 9.2 |

RESULT: prints unsupported

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
