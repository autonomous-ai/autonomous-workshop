# Overhang and support

`artifacts/make/r0001/product/cad/part_black_knight.step.py --angle 45.0 --report artifacts/make/r0001/product/cad/measure/overhang-black_knight.md`

part_black_knight.step.py: 8.0 cm2 of surface, grid 0.400 mm, 14 unsupported samples over 1 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 16.0% of the surface faces down that steeply; 0 region(s) need support, 1 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 1 region(s), longest span 0.7 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 1.4 | (-3.8, 0.1, 5.0) | 0.7 | 2.0 |

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.

## Report-format compatibility summary

RESULT: prints unsupported

Derived mechanically from the passing required table rows above; no measurements changed. Original report SHA256: 6f6bbca7b684cea274146766a368f0abca07cacee05b8256de5e01cdd91e2d9d.
