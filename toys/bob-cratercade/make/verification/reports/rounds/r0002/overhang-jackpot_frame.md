# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_jackpot_frame.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0002/overhang-jackpot_frame.md`

part_jackpot_frame.step.py: 157.1 cm2 of surface, grid 0.400 mm, 1776 unsupported samples over 10 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 22.3% of the surface faces down that steeply; 0 region(s) need support, 10 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 10 region(s), longest span 8.0 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 36.9 | (-29.8, -5.7, 4.0) | 8.0 | 5.2 |
| 2 | bridge | 26.9 | (-30.1, 9.0, 37.0) | 3.0 | 20.0 |
| 3 | bridge | 26.9 | (-29.9, -9.0, 37.0) | 3.0 | 20.0 |
| 4 | bridge | 26.8 | (54.2, 9.0, 37.0) | 3.0 | 20.0 |
| 5 | bridge | 26.6 | (54.1, -9.0, 37.0) | 3.0 | 20.0 |
| 6 | bridge | 26.5 | (54.9, -5.7, 4.0) | 6.0 | 5.2 |
| 7 | bridge | 26.3 | (-29.9, 0.0, 28.0) | 3.0 | 20.0 |
| 8 | bridge | 26.3 | (54.2, -0.0, 28.0) | 3.0 | 20.0 |

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
