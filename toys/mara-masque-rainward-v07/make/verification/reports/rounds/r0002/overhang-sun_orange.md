# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_sun_orange.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0002/overhang-sun_orange.md`

part_sun_orange.step.py: 517.9 cm2 of surface, grid 0.400 mm, 1 unsupported samples over 1 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 41.8% of the surface faces down that steeply; 0 region(s) need support, 0 bridge, 1 below 1 mm2 |
| bridges within 12 mm | PASS | 0 region(s), longest span 0.0 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | trace | 0.0 | (-80.7, 22.2, 0.7) | 0.0 | 2.0 |

RESULT: prints unsupported

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
