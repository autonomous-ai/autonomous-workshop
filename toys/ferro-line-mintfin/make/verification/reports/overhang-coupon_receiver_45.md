# Overhang and support

`artifacts/make/r0001/product/cad/part_coupon_receiver_45.step.py --angle 45.0 --report artifacts/make/r0001/product/cad/measure/overhang-coupon_receiver_45.md`

part_coupon_receiver_45.step.py: 8.8 cm2 of surface, grid 0.400 mm, 119 unsupported samples over 1 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 20.8% of the surface faces down that steeply; 0 region(s) need support, 1 bridge, 0 below 1 mm2 |
| bridges within 12 mm | PASS | 1 region(s), longest span 7.1 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 14.1 | (1.7, 0.3, 3.1) | 7.1 | 5.6 |

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.

## Workshop report-format compatibility summary

RESULT: prints unsupported

Manager-added summary of the measured check table above; original CAD-generated text is preserved verbatim. The final verifier returned exit 0. This annotation supplies the legacy summary label required by the proposal validator; it adds no measurement or physical-print claim. Original report SHA256: 7b2406b064fd4c679c7b473a520c44c9d8f3537e77d95fac75c86986928841bc.
