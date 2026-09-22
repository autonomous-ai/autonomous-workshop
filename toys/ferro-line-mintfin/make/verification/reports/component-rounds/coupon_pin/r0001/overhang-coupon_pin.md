# Overhang and support

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_coupon_pin.step.py --angle 45.0 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/coupon_pin/r0001/overhang-coupon_pin.md`

part_coupon_pin.step.py: 5.6 cm2 of surface, grid 0.400 mm, 189 unsupported samples over 4 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | FAIL | 29.1% of the surface faces down that steeply; 1 region(s) need support, 1 bridge, 2 below 1 mm2; worst 1.1 mm2 spanning 4.1 mm |
| bridges within 12 mm | PASS | 1 region(s), longest span 8.2 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 18.5 | (-0.2, -0.1, 6.5) | 8.2 | 8.0 |
| 2 | overhang | 1.1 | (0.8, 2.8, 0.3) | 4.1 | 1.6 |
| 3 | trace | 0.2 | (0.2, -4.1, 0.4) | 0.0 | 1.6 |
| 4 | trace | 0.2 | (-3.3, -2.4, 0.3) | 0.3 | 1.6 |

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.
