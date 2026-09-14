# Overhang and support

`artifacts/make/r0001/product/heritage/part_tank_cover.step.py --angle 45.0 --report artifacts/make/r0001/product/heritage/measure/overhang-tank_cover.md`

part_tank_cover.step.py: 38.0 cm2 of surface, grid 0.400 mm, 169 unsupported samples over 2 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 27.7% of the surface faces down that steeply; 0 region(s) need support, 2 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 2 region(s), longest span 3.1 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 8.4 | (0.3, 0.2, 3.2) | 3.1 | 4.4 |
| 2 | bridge | 7.9 | (18.3, 0.3, 3.2) | 3.1 | 4.4 |

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.

## Captured deterministic verdict

The original verifier report above is unchanged. The following fresh check output supplies the verdict emitted only on stdout.

```text
part_tank_cover.step.py: 38.0 cm2 of surface, grid 0.400 mm, 169 unsupported samples over 2 region(s)
  PASS  no face under 45 deg needs support     27.7% of the surface faces down that steeply; 0 region(s) need support, 2 bridge, 0 below 1 mm2
  PASS  bridges within 12 mm                   2 region(s), longest span 3.1 mm
        every unsupported region, largest first:
        1. [bridge  ]     8.4 mm2 at (0.3, 0.2, 3.2)  span   3.1 mm of 3x3, 4.4 mm of air below
        2. [bridge  ]     7.9 mm2 at (18.3, 0.3, 3.2)  span   3.1 mm of 3x3, 4.4 mm of air below
RESULT: prints unsupported

```
