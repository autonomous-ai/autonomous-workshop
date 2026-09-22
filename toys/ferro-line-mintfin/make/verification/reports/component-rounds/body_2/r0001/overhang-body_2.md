# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_body_2.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/body_2/r0001/overhang-body_2.md`

part_body_2.step.py: 17.3 cm2 of surface, grid 0.400 mm, 366 unsupported samples over 4 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | FAIL | 16.2% of the surface faces down that steeply; 1 region(s) need support, 2 bridge, 1 below 1 mm2; worst 1.1 mm2 spanning 0.6 mm |
| bridges within 12 mm | PASS | 2 region(s), longest span 8.1 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 18.5 | (17.8, -0.1, 6.4) | 8.1 | 8.0 |
| 2 | bridge | 18.2 | (1.9, 0.2, 2.6) | 7.0 | 5.6 |
| 3 | overhang | 1.1 | (8.0, 11.7, 0.3) | 0.6 | 1.6 |
| 4 | trace | 0.9 | (8.1, -11.7, 0.3) | 0.6 | 1.6 |

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
