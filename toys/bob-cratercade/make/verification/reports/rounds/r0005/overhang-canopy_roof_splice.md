# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_canopy_roof_splice.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0005/overhang-canopy_roof_splice.md`

part_canopy_roof_splice.step.py: 59.6 cm2 of surface, grid 0.400 mm, 2198 unsupported samples over 4 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 33.7% of the surface faces down that steeply; 0 region(s) need support, 4 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 4 region(s), longest span 9.4 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 83.4 | (-14.8, -13.5, 6.1) | 9.4 | 7.6 |
| 2 | bridge | 82.6 | (-14.9, 13.7, 6.1) | 9.1 | 7.6 |
| 3 | bridge | 81.5 | (15.0, 13.7, 6.1) | 9.1 | 7.6 |
| 4 | bridge | 80.8 | (15.1, -13.5, 6.1) | 9.4 | 7.6 |

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
