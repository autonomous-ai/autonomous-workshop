# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_landing_ramp.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0003/overhang-landing_ramp.md`

part_landing_ramp.step.py: 154.1 cm2 of surface, grid 0.400 mm, 1844 unsupported samples over 2 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | FAIL | 17.7% of the surface faces down that steeply; 2 region(s) need support, 0 bridge, 0 below 1 mm2; worst 177.0 mm2 spanning 5.2 mm |
| bridges within 12 mm | PASS | 0 region(s), longest span 0.0 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | overhang | 177.0 | (0.4, 100.6, 33.9) | 5.2 | 20.0 |
| 2 | overhang | 117.3 | (0.4, 67.4, 2.4) | 4.1 | 5.6 |

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
