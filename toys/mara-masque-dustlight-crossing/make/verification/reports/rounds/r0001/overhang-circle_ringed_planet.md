# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_circle_ringed_planet.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/overhang-circle_ringed_planet.md`

part_circle_ringed_planet.step.py: 17.4 cm2 of surface, grid 0.400 mm, 6 unsupported samples over 1 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 21.9% of the surface faces down that steeply; 0 region(s) need support, 0 bridge, 1 below 1 mm2 |
| bridges within 12 mm | PASS | 0 region(s), longest span 0.0 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | trace | 0.9 | (-7.6, -0.2, 11.7) | 0.6 | 8.8 |

RESULT: prints unsupported

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
