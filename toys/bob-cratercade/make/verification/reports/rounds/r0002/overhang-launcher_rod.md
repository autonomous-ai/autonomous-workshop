# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_launcher_rod.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0002/overhang-launcher_rod.md`

part_launcher_rod.step.py: 49.6 cm2 of surface, grid 0.400 mm, 5015 unsupported samples over 7 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | FAIL | 15.9% of the surface faces down that steeply; 7 region(s) need support, 0 bridge, 0 below 1 mm2; worst 492.2 mm2 spanning 8.0 mm |
| bridges within 12 mm | PASS | 0 region(s), longest span 0.0 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | overhang | 492.2 | (11.1, 40.1, 7.0) | 8.0 | 8.0 |
| 2 | overhang | 55.7 | (16.7, 80.3, 32.7) | 7.1 | 20.0 |
| 3 | overhang | 54.7 | (16.1, 4.0, 1.4) | 5.8 | 4.4 |
| 4 | overhang | 53.9 | (5.9, 4.1, 1.5) | 5.8 | 4.4 |
| 5 | overhang | 47.8 | (10.9, 74.0, 2.1) | 3.4 | 3.6 |
| 6 | overhang | 29.9 | (11.0, 78.2, 11.0) | 3.6 | 12.0 |
| 7 | overhang | 16.0 | (9.1, 44.1, 2.0) | 3.9 | 3.2 |

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
