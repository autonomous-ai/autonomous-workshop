# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_jackpot_frame.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0003/overhang-jackpot_frame.md`

part_jackpot_frame.step.py: 165.7 cm2 of surface, grid 0.400 mm, 1075 unsupported samples over 6 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 23.4% of the surface faces down that steeply; 0 region(s) need support, 6 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 6 region(s), longest span 3.0 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 26.9 | (54.1, 9.0, 37.0) | 3.0 | 20.0 |
| 2 | bridge | 26.8 | (-29.7, 9.0, 37.0) | 3.0 | 20.0 |
| 3 | bridge | 26.6 | (-30.1, -9.0, 37.0) | 3.0 | 20.0 |
| 4 | bridge | 26.6 | (53.8, -9.0, 37.0) | 3.0 | 20.0 |
| 5 | bridge | 26.3 | (-29.8, -0.0, 28.0) | 3.0 | 20.0 |
| 6 | bridge | 26.3 | (54.1, 0.0, 28.0) | 3.0 | 20.0 |

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
