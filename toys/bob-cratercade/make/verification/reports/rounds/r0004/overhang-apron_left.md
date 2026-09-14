# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_apron_left.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0004/overhang-apron_left.md`

part_apron_left.step.py: 280.3 cm2 of surface, grid 0.400 mm, 1080 unsupported samples over 34 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 20.9% of the surface faces down that steeply; 0 region(s) need support, 3 bridge, 31 below 1 mm2 |
| bridges within 12 mm | PASS | 3 region(s), longest span 9.7 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 124.4 | (84.0, -40.5, 1.5) | 0.9 | 2.8 |
| 2 | bridge | 8.0 | (22.9, -11.3, 22.5) | 9.7 | 20.0 |
| 3 | bridge | 7.7 | (151.0, -9.2, 22.5) | 9.6 | 20.0 |
| 4 | trace | 0.1 | (51.9, -38.2, 15.5) | 0.2 | 12.4 |
| 5 | trace | 0.1 | (66.2, -38.0, 15.4) | 0.0 | 6.8 |
| 6 | trace | 0.0 | (26.7, -23.1, 15.5) | 3.4 | 12.4 |
| 7 | trace | 0.0 | (76.1, -37.8, 15.4) | 0.0 | 6.8 |
| 8 | trace | 0.0 | (34.8, -25.7, 15.4) | 0.0 | 12.0 |

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
