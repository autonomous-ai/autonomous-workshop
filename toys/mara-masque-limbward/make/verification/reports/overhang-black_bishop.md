# Overhang and support

`artifacts/make/r0001/product/cad/part_black_bishop.step.py --angle 45.0 --report artifacts/make/r0001/product/cad/measure/overhang-black_bishop.md`

part_black_bishop.step.py: 15.1 cm2 of surface, grid 0.400 mm, 5 unsupported samples over 2 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 11.8% of the surface faces down that steeply; 0 region(s) need support, 0 bridge, 2 below 1 mm2 |
| bridges within 12 mm | PASS | 0 region(s), longest span 0.0 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | trace | 0.1 | (-3.2, -5.1, 3.0) | 0.0 | 4.0 |
| 2 | trace | 0.0 | (-3.2, 5.2, 3.0) | 0.0 | 4.0 |

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.

## Recorded tool stdout verdict

RESULT: prints unsupported

Recorded in `measure/rounds/r0001/overhang-black_bishop.log` (sha256 cc0e430c3847dd18f09a5e9814014078226729ed05900e5ea65d4c1d2a163ef3). The final verifier reran the same geometry and returned exit 0; report measurement bodies match.
