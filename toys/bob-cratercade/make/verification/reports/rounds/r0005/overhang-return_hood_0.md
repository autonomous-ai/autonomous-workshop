# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_return_hood_0.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0005/overhang-return_hood_0.md`

part_return_hood_0.step.py: 211.2 cm2 of surface, grid 0.400 mm, 454 unsupported samples over 2 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 15.4% of the surface faces down that steeply; 0 region(s) need support, 2 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 2 region(s), longest span 7.1 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 28.8 | (51.0, 17.2, 16.0) | 7.1 | 17.2 |
| 2 | bridge | 28.5 | (33.2, 91.5, 16.0) | 7.0 | 17.2 |

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
