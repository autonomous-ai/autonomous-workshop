# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_bull_muzzle.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/bull_muzzle/r0001/overhang-bull_muzzle.md`

part_bull_muzzle.step.py: 19.7 cm2 of surface, grid 0.400 mm, 177 unsupported samples over 4 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | FAIL | 25.7% of the surface faces down that steeply; 4 region(s) need support, 0 bridge, 0 below 1 mm2; worst 13.1 mm2 spanning 2.1 mm |
| bridges within 12 mm | PASS | 0 region(s), longest span 0.0 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | overhang | 13.1 | (-0.5, -11.5, 1.9) | 2.1 | 4.4 |
| 2 | overhang | 8.4 | (-0.7, 11.7, 2.0) | 1.8 | 4.4 |
| 3 | overhang | 3.7 | (-17.6, -0.2, 1.8) | 1.6 | 4.0 |
| 4 | overhang | 2.0 | (17.7, 1.0, 2.0) | 1.3 | 4.0 |

RESULT: NEEDS SUPPORT

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
