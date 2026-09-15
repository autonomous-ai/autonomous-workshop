# Overhang and support

`artifacts/make/r0001/product/cad/part_black_king.step.py --angle 45.0 --report artifacts/make/r0001/product/cad/measure/overhang-black_king.md`

part_black_king.step.py: 9.9 cm2 of surface, grid 0.400 mm, 8 unsupported samples over 3 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 12.9% of the surface faces down that steeply; 0 region(s) need support, 0 bridge, 3 below 1 mm2 |
| bridges within 12 mm | PASS | 0 region(s), longest span 0.0 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | trace | 0.1 | (-2.8, -2.9, 18.0) | 0.1 | 15.2 |
| 2 | trace | 0.1 | (2.8, -2.9, 18.0) | 0.2 | 15.2 |
| 3 | trace | 0.0 | (-2.9, 3.0, 18.0) | 0.0 | 15.2 |

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.

## Report-format compatibility summary

RESULT: prints unsupported

Derived mechanically from the passing required table rows above; no measurements changed. Original report SHA256: 5a5c7b2c1eec19d7fa5111e4cd899c8d62366a6d692d3983a79fa5862298899b.
