# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_bear_body.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/bear_body/r0002/overhang-bear_body.md`

part_bear_body.step.py: 160.0 cm2 of surface, grid 0.400 mm, 1334 unsupported samples over 9 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 25.9% of the surface faces down that steeply; 0 region(s) need support, 7 bridge, 2 below 1 mm2 |
| bridges within 12 mm | PASS | 7 region(s), longest span 8.0 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 46.0 | (-10.7, -18.3, 1.3) | 8.0 | 2.4 |
| 2 | bridge | 36.4 | (25.3, -31.2, 1.3) | 6.7 | 2.4 |
| 3 | bridge | 35.8 | (-24.9, -31.3, 1.3) | 6.5 | 2.4 |
| 4 | bridge | 23.5 | (-0.0, 30.4, 27.2) | 2.7 | 20.0 |
| 5 | bridge | 19.4 | (27.3, -26.2, 20.6) | 2.6 | 6.4 |
| 6 | bridge | 18.9 | (-26.8, -26.5, 20.6) | 2.5 | 6.4 |
| 7 | bridge | 4.7 | (-10.6, -3.0, 1.3) | 0.8 | 2.4 |
| 8 | trace | 0.9 | (-30.7, -26.6, 13.0) | 0.9 | 14.0 |

RESULT: prints unsupported

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
