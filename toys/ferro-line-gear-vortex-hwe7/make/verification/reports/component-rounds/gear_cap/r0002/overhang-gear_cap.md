# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/part_gear_cap.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/measure/component-rounds/gear_cap/r0002/overhang-gear_cap.md`

part_gear_cap.step.py: 2.2 cm2 of surface, grid 0.400 mm, 44 unsupported samples over 1 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | FAIL | 11.3% of the surface faces down that steeply; 1 region(s) need support, 0 bridge, 0 below 1 mm2; worst 1.9 mm2 spanning 4.6 mm |
| bridges within 12 mm | PASS | 0 region(s), longest span 0.0 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | overhang | 1.9 | (0.1, 0.0, 0.5) | 4.6 | 2.0 |

RESULT: NEEDS SUPPORT

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
