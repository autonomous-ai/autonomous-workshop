# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_white_queen.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/white_queen/r0001/overhang-white_queen.md`

part_white_queen.step.py: 11.7 cm2 of surface, grid 0.400 mm, 11 unsupported samples over 2 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 13.1% of the surface faces down that steeply; 0 region(s) need support, 0 bridge, 2 below 1 mm2 |
| bridges within 12 mm | PASS | 0 region(s), longest span 0.0 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | trace | 0.0 | (0.6, -4.9, 23.0) | 0.4 | 20.0 |
| 2 | trace | 0.0 | (-0.6, 2.9, 23.0) | 2.3 | 20.0 |

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
