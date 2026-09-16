# Overhang and support

`artifacts/make/r0001/product/cad/part_anchor.step.py --angle 45.0 --report artifacts/make/r0001/product/cad/measure/overhang-anchor.md`

part_anchor.step.py: 4.3 cm2 of surface, grid 0.400 mm, 16 unsupported samples over 1 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 21.6% of the surface faces down that steeply; 0 region(s) need support, 1 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 1 region(s), longest span 0.8 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 1.9 | (-0.5, -0.9, 10.5) | 0.8 | 3.2 |

RESULT: prints unsupported

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
