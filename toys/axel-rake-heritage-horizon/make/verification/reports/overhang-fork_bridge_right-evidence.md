# Overhang and support

`artifacts/make/r0001/product/heritage/part_fork_bridge_right.step.py --angle 45.0 --report artifacts/make/r0001/product/heritage/measure/overhang-fork_bridge_right.md`

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

## Captured deterministic verdict

The original verifier report above is unchanged. The following fresh check output supplies the verdict emitted only on stdout.

```text
part_fork_bridge_right.step.py: 10.5 cm2 of surface, grid 0.400 mm, 100 unsupported samples over 1 region(s)
  PASS  no face under 45 deg needs support     22.6% of the surface faces down that steeply; 0 region(s) need support, 1 bridge, 0 below 1 mm2
  PASS  bridges within 12 mm                   1 region(s), longest span 3.3 mm
        every unsupported region, largest first:
        1. [bridge  ]    15.6 mm2 at (47.0, 75.7, 4.2)  span   3.3 mm of 3x6, 5.2 mm of air below
RESULT: prints unsupported

```
