# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_corona_cell.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/corona_cell/r0003/overhang-corona_cell.md`

part_corona_cell.step.py: 33.2 cm2 of surface, grid 0.400 mm, 636 unsupported samples over 2 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | FAIL | 39.0% of the surface faces down that steeply; 2 region(s) need support, 0 bridge, 0 below 1 mm2; worst 50.1 mm2 spanning 14.6 mm |
| bridges within 12 mm | PASS | 0 region(s), longest span 0.0 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | overhang | 50.1 | (2.2, 6.3, 2.6) | 14.6 | 0.8 |
| 2 | overhang | 48.1 | (-1.7, -6.2, 2.6) | 15.3 | 0.8 |

RESULT: NEEDS SUPPORT

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
