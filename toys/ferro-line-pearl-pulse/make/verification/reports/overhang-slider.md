# Overhang and support

`artifacts/make/r0001/product/cad/part_slider.step.py --angle 45.0 --report artifacts/make/r0001/product/cad/measure/overhang-slider.md`

part_slider.step.py: 43.2 cm2 of surface, grid 0.400 mm, 194 unsupported samples over 3 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 26.6% of the surface faces down that steeply; 0 region(s) need support, 3 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 3 region(s), longest span 3.9 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 4.3 | (23.2, 9.7, 24.9) | 3.6 | 20.0 |
| 2 | bridge | 4.1 | (-3.5, -25.2, 24.9) | 2.7 | 20.0 |
| 3 | bridge | 3.8 | (-20.3, 15.2, 24.9) | 3.9 | 20.0 |

RESULT: prints unsupported

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
