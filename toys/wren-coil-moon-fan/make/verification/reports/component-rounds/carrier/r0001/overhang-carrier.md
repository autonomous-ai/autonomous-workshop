# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_carrier.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/carrier/r0001/overhang-carrier.md`

part_carrier.step.py: 55.4 cm2 of surface, grid 0.400 mm, 117 unsupported samples over 2 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 34.9% of the surface faces down that steeply; 0 region(s) need support, 2 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 2 region(s), longest span 1.0 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 9.7 | (-26.9, 17.3, 3.6) | 1.0 | 1.6 |
| 2 | bridge | 8.6 | (-26.6, -17.1, 3.6) | 1.0 | 1.6 |

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
