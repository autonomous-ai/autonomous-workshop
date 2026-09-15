# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_landing_ramp.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0002/overhang-landing_ramp.md`

part_landing_ramp.step.py: 145.8 cm2 of surface, grid 0.400 mm, 17641 unsupported samples over 7 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | FAIL | 19.7% of the surface faces down that steeply; 4 region(s) need support, 1 bridge, 2 below 1 mm2; worst 1888.1 mm2 spanning 45.6 mm |
| bridges within 12 mm | PASS | 1 region(s), longest span 3.0 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | overhang | 1888.1 | (16.6, 54.0, -0.0) | 45.6 | 15.2 |
| 2 | overhang | 860.3 | (23.7, 55.4, 29.6) | 45.1 | 20.0 |
| 3 | overhang | 24.6 | (3.1, 60.3, -13.0) | 3.6 | 3.2 |
| 4 | overhang | 24.2 | (3.0, 67.7, -13.0) | 3.5 | 3.2 |
| 5 | bridge | 16.6 | (2.7, 64.0, 40.5) | 3.0 | 20.0 |
| 6 | trace | 0.2 | (0.2, 69.4, 32.1) | 0.0 | 20.0 |
| 7 | trace | 0.2 | (0.2, 58.2, 32.5) | 0.0 | 20.0 |

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
