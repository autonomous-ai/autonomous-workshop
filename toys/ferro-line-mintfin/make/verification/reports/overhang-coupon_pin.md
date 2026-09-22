# Overhang and support

`artifacts/make/r0001/product/cad/part_coupon_pin.step.py --angle 45.0 --report artifacts/make/r0001/product/cad/measure/overhang-coupon_pin.md`

part_coupon_pin.step.py: 5.6 cm2 of surface, grid 0.400 mm, 175 unsupported samples over 1 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 28.1% of the surface faces down that steeply; 0 region(s) need support, 1 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 1 region(s), longest span 7.8 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 18.5 | (-0.2, -0.0, 6.5) | 7.8 | 8.0 |

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.

## Workshop report-format compatibility summary

RESULT: prints unsupported

Manager-added summary of the measured check table above; original CAD-generated text is preserved verbatim. The final verifier returned exit 0. This annotation supplies the legacy summary label required by the proposal validator; it adds no measurement or physical-print claim. Original report SHA256: 6d15d15eea84e8f1cfc159cc609596ed622dcf550f37cb37d3a89e160b233430.
