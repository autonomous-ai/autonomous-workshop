# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/part_pedestal.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/measure/component-rounds/pedestal/r0001/overhang-pedestal.md`

part_pedestal.step.py: 271.2 cm2 of surface, grid 0.400 mm, 3374 unsupported samples over 2 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | FAIL | 31.7% of the surface faces down that steeply; 2 region(s) need support, 0 bridge, 0 below 1 mm2; worst 458.5 mm2 spanning 99.0 mm |
| bridges within 12 mm | PASS | 0 region(s), longest span 0.0 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | overhang | 458.5 | (0.2, 0.1, 0.8) | 99.0 | 2.0 |
| 2 | overhang | 64.7 | (0.3, 0.1, 3.0) | 12.1 | 4.0 |

RESULT: NEEDS SUPPORT

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
