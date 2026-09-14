# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_landing_ramp.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0004/overhang-landing_ramp.md`

part_landing_ramp.step.py: 163.9 cm2 of surface, grid 0.400 mm, 4333 unsupported samples over 6 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 15.1% of the surface faces down that steeply; 0 region(s) need support, 6 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 6 region(s), longest span 6.3 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 202.9 | (-0.1, 49.1, 1.5) | 6.3 | 2.4 |
| 2 | bridge | 153.4 | (-3.3, 63.6, 1.5) | 3.3 | 2.4 |
| 3 | bridge | 106.9 | (-0.4, 11.6, 1.5) | 3.3 | 2.4 |
| 4 | bridge | 105.8 | (-0.2, 37.6, 1.5) | 3.3 | 2.4 |
| 5 | bridge | 101.0 | (-0.1, 24.7, 1.5) | 3.4 | 2.4 |
| 6 | bridge | 19.5 | (26.7, 63.5, 1.4) | 3.3 | 2.4 |

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
