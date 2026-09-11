# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/crema_click/part_foot_plug.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/crema_click/measure/rounds/r0001/overhang-foot_plug.md`

part_foot_plug.step.py: 64.2 cm2 of surface, grid 0.400 mm, 410 unsupported samples over 3 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | FAIL | 39.4% of the surface faces down that steeply; 3 region(s) need support, 0 bridge, 0 below 1 mm2; worst 23.0 mm2 spanning 2.3 mm |
| bridges within 12 mm | PASS | 0 region(s), longest span 0.0 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | overhang | 23.0 | (0.0, -25.1, 8.0) | 2.3 | 2.4 |
| 2 | overhang | 22.8 | (-21.9, 12.4, 8.0) | 6.4 | 2.4 |
| 3 | overhang | 19.6 | (21.7, 12.8, 8.0) | 5.6 | 2.4 |

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
