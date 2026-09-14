# Overhang and support

`part_access_frame.step.py --angle 45.0 --report measure/overhang-access_frame.md`

part_access_frame.step.py: 269.0 cm2 of surface, grid 0.420 mm, 704 unsupported samples over 2 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 25.4% of the surface faces down that steeply; 0 region(s) need support, 2 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 2 region(s), longest span 5.4 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 59.8 | (8.9, 31.8, 17.4) | 5.4 | 18.9 |
| 2 | bridge | 59.8 | (8.9, 111.8, 17.4) | 5.4 | 18.9 |

RESULT: prints unsupported

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
