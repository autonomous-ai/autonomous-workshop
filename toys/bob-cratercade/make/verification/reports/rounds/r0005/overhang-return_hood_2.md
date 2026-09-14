# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_return_hood_2.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0005/overhang-return_hood_2.md`

part_return_hood_2.step.py: 192.8 cm2 of surface, grid 0.400 mm, 1137 unsupported samples over 3 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 17.3% of the surface faces down that steeply; 0 region(s) need support, 3 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 3 region(s), longest span 11.6 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 93.8 | (29.1, 43.8, 2.5) | 11.6 | 3.6 |
| 2 | bridge | 29.8 | (7.1, 16.5, 16.0) | 7.3 | 17.2 |
| 3 | bridge | 29.5 | (43.1, 93.5, 16.0) | 7.2 | 17.2 |

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
