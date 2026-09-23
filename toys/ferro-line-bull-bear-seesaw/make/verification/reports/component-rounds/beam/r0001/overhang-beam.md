# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_beam.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/beam/r0001/overhang-beam.md`

part_beam.step.py: 95.5 cm2 of surface, grid 0.400 mm, 2090 unsupported samples over 2 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 27.3% of the surface faces down that steeply; 0 region(s) need support, 2 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 2 region(s), longest span 12.0 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 162.0 | (-59.7, -0.0, 8.0) | 12.0 | 9.2 |
| 2 | bridge | 161.4 | (60.2, 0.1, 8.0) | 12.0 | 9.2 |

RESULT: prints unsupported

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
