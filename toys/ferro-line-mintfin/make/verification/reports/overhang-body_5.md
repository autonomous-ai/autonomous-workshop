# Overhang and support

`artifacts/make/r0001/product/cad/part_body_5.step.py --angle 45.0 --report artifacts/make/r0001/product/cad/measure/overhang-body_5.md`

part_body_5.step.py: 15.4 cm2 of surface, grid 0.400 mm, 332 unsupported samples over 4 region(s)

| check | status | detail |
|---|---|---|
| no face under 45 deg needs support | PASS | 16.7% of the surface faces down that steeply; 0 region(s) need support, 2 bridge, 2 below 1 mm2 |
| bridges within 12 mm | PASS | 2 region(s), longest span 8.2 mm |


## Unsupported regions, largest first

A `bridge` is a steep region short enough to span with material on both sides of it -- a bore ceiling or a slot roof. An `overhang` has neither, and needs support or a design change.

| # | kind | area mm2 | at | span mm | air below mm |
|---|---|---|---|---|---|
| 1 | bridge | 18.5 | (17.8, -0.1, 6.5) | 8.2 | 8.0 |
| 2 | bridge | 15.5 | (1.7, 0.4, 2.8) | 6.7 | 5.6 |
| 3 | trace | 0.8 | (8.0, 10.4, 0.3) | 0.2 | 1.6 |
| 4 | trace | 0.8 | (8.0, -10.3, 0.3) | 0.2 | 1.6 |

Measured on the entry's tessellated solid, in the pose it is printed in. The
fix belongs in
the generator: reorient the part, replace a round horizontal bore with a
teardrop, or add a 45 deg buttress under the feature.

## Workshop report-format compatibility summary

RESULT: prints unsupported

Manager-added summary of the measured check table above; original CAD-generated text is preserved verbatim. The final verifier returned exit 0. This annotation supplies the legacy summary label required by the proposal validator; it adds no measurement or physical-print claim. Original report SHA256: b87c23217a2e29b900648e25eaba9e1307af9dc39bc84ee7aab8d92a9ae340df.
