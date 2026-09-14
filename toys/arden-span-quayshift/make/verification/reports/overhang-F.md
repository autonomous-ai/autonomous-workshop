# Overhang and support

`artifacts/make/r0001/product/cad/part_F.step.py --angle 45.0 --report artifacts/make/r0001/product/cad/measure/overhang-F.md`

part_F.step.py: 145.4 cm2 of surface, grid 0.400 mm, 362 unsupported samples over 3 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 13.9% of the surface faces down that steeply; 0 region(s) need support, 3 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 3 region(s), longest span 2.9 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 16.7 | (3.5, 21.6, 26.0) | 2.9 | 20.0 |
| 2 | bridge | 16.5 | (47.8, 21.2, 38.7) | 2.9 | 16.0 |
| 3 | bridge | 16.5 | (15.8, 11.2, 30.6) | 2.9 | 20.0 |

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.

## Proposal-format compatibility summary

The current source checker emitted the passing tables above and exited zero in the final verification pipeline. Its original bytes are preserved in the run evidence. The proposal parser requires this legacy result spelling; it summarizes source print checks only and does not establish a manufactured sample.

RESULT: prints unsupported
