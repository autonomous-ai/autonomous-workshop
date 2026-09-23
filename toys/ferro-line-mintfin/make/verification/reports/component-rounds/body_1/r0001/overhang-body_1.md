# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_body_1.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/body_1/r0001/overhang-body_1.md`

part_body_1.step.py: 19.9 cm2 of surface, grid 0.400 mm, 345 unsupported samples over 6 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 18.6% of the surface faces down that steeply; 0 region(s) need support, 2 bridge, 4 below 1 mm2 |
| bridges within 12 mm | PASS | 2 region(s), longest span 8.1 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 18.5 | (17.8, -0.1, 6.5) | 8.1 | 8.0 |
| 2 | bridge | 17.5 | (1.9, 0.2, 2.7) | 7.1 | 5.6 |
| 3 | trace | 0.7 | (20.6, 2.4, 0.3) | 3.6 | 1.6 |
| 4 | trace | 0.6 | (17.0, -3.6, 0.2) | 1.5 | 1.2 |
| 5 | trace | 0.1 | (21.8, -1.5, 0.3) | 0.0 | 1.2 |
| 6 | trace | 0.1 | (15.1, 2.9, 0.3) | 0.0 | 1.6 |

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
