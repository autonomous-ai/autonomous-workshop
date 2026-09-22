# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_corona_cell.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0002/overhang-corona_cell.md`

part_corona_cell.step.py: 28.6 cm2 of surface, grid 0.400 mm, 10 unsupported samples over 2 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 39.3% of the surface faces down that steeply; 0 region(s) need support, 0 bridge, 2 below 1 mm2 |
| bridges within 12 mm | PASS | 0 region(s), longest span 0.0 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | trace | 0.0 | (-15.5, 15.5, 3.0) | 2.7 | 4.0 |
| 2 | trace | 0.0 | (16.8, 14.4, 3.0) | 0.0 | 4.0 |

RESULT: prints unsupported

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
