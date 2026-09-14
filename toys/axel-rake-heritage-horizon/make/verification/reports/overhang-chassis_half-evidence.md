# Overhang and support

`artifacts/make/r0001/product/heritage/part_chassis_half.step.py --angle 45.0 --report artifacts/make/r0001/product/heritage/measure/overhang-chassis_half.md`

part_chassis_half.step.py: 108.3 cm2 of surface, grid 0.400 mm, 351 unsupported samples over 4 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 25.1% of the surface faces down that steeply; 0 region(s) need support, 2 bridge, 2 below 1 mm2 |
| bridges within 12 mm | PASS | 2 region(s), longest span 5.9 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 53.1 | (35.5, -65.8, 5.2) | 5.9 | 6.4 |
| 2 | bridge | 2.0 | (10.0, -32.9, 15.4) | 0.9 | 2.4 |
| 3 | trace | 0.5 | (13.7, -37.8, 15.4) | 0.1 | 2.4 |
| 4 | trace | 0.1 | (-9.9, -32.7, 15.4) | 0.0 | 2.4 |

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.

## Captured deterministic verdict

The original verifier report above is unchanged. The following fresh check output supplies the verdict emitted only on stdout.

```text
part_chassis_half.step.py: 108.3 cm2 of surface, grid 0.400 mm, 351 unsupported samples over 4 region(s)
  PASS  no face under 45 deg needs support     25.1% of the surface faces down that steeply; 0 region(s) need support, 2 bridge, 2 below 1 mm2
  PASS  bridges within 12 mm                   2 region(s), longest span 5.9 mm
        every unsupported region, largest first:
        1. [bridge  ]    53.1 mm2 at (35.5, -65.8, 5.2)  span   5.9 mm of 9x6, 6.4 mm of air below
        2. [bridge  ]     2.0 mm2 at (10.0, -32.9, 15.4)  span   0.9 mm of 2x1, 2.4 mm of air below
        3. [trace   ]     0.5 mm2 at (13.7, -37.8, 15.4)  span   0.1 mm of 0x1, 2.4 mm of air below
        4. [trace   ]     0.1 mm2 at (-9.9, -32.7, 15.4)  span   0.0 mm of 0x0, 2.4 mm of air below
RESULT: prints unsupported

```
