# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_base.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/overhang-base.md`

part_base.step.py: 186.4 cm2 of surface, grid 0.400 mm, 96 unsupported samples over 1 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 41.1% of the surface faces down that steeply; 0 region(s) need support, 1 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 1 region(s), longest span 2.0 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 14.0 | (-0.1, 11.4, 16.9) | 2.0 | 11.2 |

RESULT: prints unsupported

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
