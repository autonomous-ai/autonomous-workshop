# Thickness and hollow

`artifacts/make/r0001/product/cad/part_coupon_receiver_35.step.py --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-coupon_receiver_35.md`

part_coupon_receiver_35.step.py: 0.84 cm3 solid, grid 0.133 mm (173x113x63), 45349 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (10 of 45349 samples); thinnest 0.13 mm at (-4.4, -5.6, 7.7) in 3 region(s); no region is a wall, 3 taper(s) at feature edges (0.02% of surface, budget 2%); 3 more within measurement error of the limit |
| thickness distribution | PASS | median 3.33 mm, p95 10.00 mm, max 22.20 mm |
| hollowable at 1.20 mm wall | WARN | 0.08 of 0.84 cm3 (9%) in 1 pocket(s) |
| filament that would save | PASS | 0.01 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.53 mm | (-4.4, 5.7, 7.5) | 5 | 0.1 | 0.5 | 0.20 |
| 2 | taper | 0.13 mm | (-4.4, -5.6, 7.7) | 4 | 0.1 | 0.5 | 0.14 |
| 3 | taper | 0.20 mm | (-2.7, -3.5, 6.5) | 1 | 0.0 | 0.0 | 0.14 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.

## Workshop report-format compatibility summary

RESULT: printable at this wall

Manager-added summary of the measured check table above; original CAD-generated text is preserved verbatim. The final verifier returned exit 0. This annotation supplies the legacy summary label required by the proposal validator; it adds no measurement or physical-print claim. Original report SHA256: a3eda4c7dd267cb26b163e5657b68bf3ee1b92153f21ac881eb76df34adc3b7b.
