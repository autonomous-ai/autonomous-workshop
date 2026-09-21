# Overhang and support

`.tmp/trial-kingdown/part_kingdown.step.py --angle 45 --report artifacts/make/r0001/product/cad/review/trial-b-counter-king-face-down-overhang.md`

part_kingdown.step.py: 8.7 cm2 of surface, grid 0.400 mm, 807 unsupported samples over 1 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | FAIL | 23.0% of the surface faces down that steeply; 1 region(s) need support, 0 bridge, 0 below 1 mm2; worst 120.9 mm2 spanning 15.8 mm |
| bridges within 12 mm | PASS | 0 region(s), longest span 0.0 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | overhang | 120.9 | (0.0, -0.1, 1.2) | 15.8 | 2.4 |

RESULT: NEEDS SUPPORT

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
