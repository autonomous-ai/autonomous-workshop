# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_landing_ramp.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0009/overhang-landing_ramp.md`

part_landing_ramp.step.py: 166.6 cm2 of surface, grid 0.400 mm, 4338 unsupported samples over 7 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 13.7% of the surface faces down that steeply; 0 region(s) need support, 7 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 7 region(s), longest span 3.4 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 154.0 | (-3.8, 63.6, 1.5) | 3.3 | 2.4 |
| 2 | bridge | 107.8 | (-0.1, 11.6, 1.5) | 3.3 | 2.4 |
| 3 | bridge | 107.4 | (-0.2, 37.5, 1.5) | 3.4 | 2.4 |
| 4 | bridge | 100.6 | (-0.3, 44.7, 1.5) | 3.4 | 2.4 |
| 5 | bridge | 100.3 | (-0.7, 50.6, 1.5) | 3.3 | 2.4 |
| 6 | bridge | 99.4 | (-0.3, 24.7, 1.5) | 3.1 | 2.4 |
| 7 | bridge | 20.3 | (26.8, 63.5, 1.4) | 3.3 | 2.4 |

RESULT: prints unsupported

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
