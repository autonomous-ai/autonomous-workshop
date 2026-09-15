# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_flipper_right_rotor.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0002/overhang-flipper_right_rotor.md`

part_flipper_right_rotor.step.py: 69.7 cm2 of surface, grid 0.400 mm, 176 unsupported samples over 1 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 29.2% of the surface faces down that steeply; 0 region(s) need support, 1 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 1 region(s), longest span 7.8 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 20.2 | (-0.1, -30.2, 13.0) | 7.8 | 4.8 |

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
