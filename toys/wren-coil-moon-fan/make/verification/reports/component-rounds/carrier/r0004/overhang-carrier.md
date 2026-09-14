# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_carrier.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/carrier/r0004/overhang-carrier.md`

part_carrier.step.py: 73.2 cm2 of surface, grid 0.400 mm, 619 unsupported samples over 3 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | FAIL | 36.6% of the surface faces down that steeply; 1 region(s) need support, 2 bridge, 0 below 1 mm2; worst 86.0 mm2 spanning 17.5 mm |
| bridges within 12 mm | PASS | 2 region(s), longest span 0.8 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | overhang | 86.0 | (-28.4, 0.2, 0.4) | 17.5 | 1.6 |
| 2 | bridge | 7.3 | (-28.3, 17.4, 3.6) | 0.8 | 1.6 |
| 3 | bridge | 5.0 | (-28.2, -17.2, 3.5) | 0.5 | 1.6 |

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
