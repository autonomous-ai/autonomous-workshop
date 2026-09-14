# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_launcher_housing.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0002/overhang-launcher_housing.md`

part_launcher_housing.step.py: 239.4 cm2 of surface, grid 0.400 mm, 1789 unsupported samples over 4 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 20.9% of the surface faces down that steeply; 0 region(s) need support, 4 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 4 region(s), longest span 8.1 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 93.1 | (12.4, 156.5, 13.0) | 7.4 | 14.0 |
| 2 | bridge | 59.1 | (9.8, 32.0, 13.0) | 7.3 | 14.0 |
| 3 | bridge | 52.1 | (28.2, 14.4, 5.2) | 7.8 | 6.4 |
| 4 | bridge | 51.4 | (28.0, 37.7, 5.2) | 8.1 | 6.4 |

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
