# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/heritage/part_fork_bridge_right.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/heritage/measure/component-rounds/fork_bridge_right/r0001/overhang-fork_bridge_right.md`

part_fork_bridge_right.step.py: 10.5 cm2 of surface, grid 0.400 mm, 100 unsupported samples over 1 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 22.6% of the surface faces down that steeply; 0 region(s) need support, 1 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 1 region(s), longest span 3.3 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 15.6 | (47.0, 75.7, 4.2) | 3.3 | 5.2 |

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
