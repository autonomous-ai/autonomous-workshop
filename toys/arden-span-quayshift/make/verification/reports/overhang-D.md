# Overhang and support

`artifacts/make/r0001/product/cad/part_D.step.py --angle 45.0 --report artifacts/make/r0001/product/cad/measure/overhang-D.md`

part_D.step.py: 203.1 cm2 of surface, grid 0.400 mm, 434 unsupported samples over 4 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 14.9% of the surface faces down that steeply; 0 region(s) need support, 4 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 4 region(s), longest span 3.0 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 18.0 | (3.4, 42.9, 26.0) | 3.0 | 20.0 |
| 2 | bridge | 16.5 | (15.8, 25.4, 30.7) | 3.0 | 20.0 |
| 3 | bridge | 14.1 | (9.7, 25.5, 50.7) | 2.9 | 20.0 |
| 4 | bridge | 14.1 | (21.9, 25.4, 50.7) | 2.9 | 20.0 |

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.

## Proposal-format compatibility summary

The current source checker emitted the passing tables above and exited zero in the final verification pipeline. Its original bytes are preserved in the run evidence. The proposal parser requires this legacy result spelling; it summarizes source print checks only and does not establish a manufactured sample.

RESULT: prints unsupported
