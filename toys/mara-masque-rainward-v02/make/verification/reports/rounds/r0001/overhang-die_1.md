# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_die_1.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/overhang-die_1.md`

part_die_1.step.py: 16.0 cm2 of surface, grid 0.400 mm, 835 unsupported samples over 16 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | FAIL | 16.7% of the surface faces down that steeply; 2 region(s) need support, 0 bridge, 14 below 1 mm2; worst 9.4 mm2 spanning 2.0 mm |
| bridges within 12 mm | PASS | 0 region(s), longest span 0.0 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | overhang | 9.4 | (-3.9, -0.1, 0.5) | 2.0 | 1.6 |
| 2 | overhang | 9.4 | (4.2, -0.2, 0.5) | 2.0 | 1.6 |
| 3 | trace | 0.8 | (-7.8, 4.0, 12.9) | 0.5 | 14.0 |
| 4 | trace | 0.8 | (-7.8, 4.0, 4.9) | 0.5 | 6.0 |
| 5 | trace | 0.8 | (-7.8, -4.0, 4.9) | 0.5 | 6.0 |
| 6 | trace | 0.8 | (-7.8, -4.0, 12.9) | 0.5 | 14.0 |
| 7 | trace | 0.8 | (-7.7, -0.0, 8.9) | 0.5 | 10.0 |
| 8 | trace | 0.8 | (-0.0, 7.7, 8.9) | 0.5 | 2.0 |

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
