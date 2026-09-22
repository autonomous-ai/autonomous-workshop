# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/part_pedestal_lid.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/measure/component-rounds/pedestal_lid/r0001/overhang-pedestal_lid.md`

part_pedestal_lid.step.py: 178.7 cm2 of surface, grid 0.400 mm, 1229 unsupported samples over 4 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | FAIL | 42.9% of the surface faces down that steeply; 3 region(s) need support, 1 bridge, 0 below 1 mm2; worst 19.2 mm2 spanning 6.1 mm |
| bridges within 12 mm | PASS | 1 region(s), longest span 5.9 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 141.1 | (0.1, 0.0, 1.0) | 5.9 | 2.0 |
| 2 | overhang | 19.2 | (-25.0, -43.2, 5.0) | 6.1 | 6.8 |
| 3 | overhang | 18.3 | (-24.9, 43.3, 5.0) | 5.9 | 6.8 |
| 4 | overhang | 16.6 | (50.0, -0.0, 5.1) | 1.7 | 6.8 |

RESULT: NEEDS SUPPORT

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
