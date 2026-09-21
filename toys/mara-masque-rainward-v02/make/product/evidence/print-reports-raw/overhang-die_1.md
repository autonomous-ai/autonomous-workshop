# Overhang and support

`artifacts/make/r0001/product/cad/part_die_1.step.py --angle 45.0 --report artifacts/make/r0001/product/cad/measure/overhang-die_1.md`

part_die_1.step.py: 15.7 cm2 of surface, grid 0.400 mm, 385 unsupported samples over 14 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 15.6% of the surface faces down that steeply; 0 region(s) need support, 0 bridge, 14 below 1 mm2 |
| bridges within 12 mm | PASS | 0 region(s), longest span 0.0 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | trace | 0.5 | (-7.6, -0.0, 8.6) | 0.5 | 10.0 |
| 2 | trace | 0.5 | (-4.0, -7.6, 4.6) | 0.5 | 6.0 |
| 3 | trace | 0.5 | (-7.6, 4.0, 12.7) | 0.5 | 14.0 |
| 4 | trace | 0.5 | (-4.0, -7.6, 12.6) | 0.5 | 14.0 |
| 5 | trace | 0.5 | (-7.6, -4.0, 4.6) | 0.5 | 6.0 |
| 6 | trace | 0.5 | (-7.6, 4.0, 4.7) | 0.5 | 6.0 |
| 7 | trace | 0.5 | (4.0, -7.6, 12.6) | 0.4 | 14.0 |
| 8 | trace | 0.4 | (-4.0, 7.6, 12.7) | 0.5 | 1.6 |

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
