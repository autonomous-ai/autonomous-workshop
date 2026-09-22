# Thickness and hollow

`artifacts/make/r0001/product/cad/part_coupon_receiver_45.step.py --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-coupon_receiver_45.md`

part_coupon_receiver_45.step.py: 0.81 cm3 solid, grid 0.133 mm (173x113x63), 45336 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (9 of 45336 samples); thinnest 0.13 mm at (-2.9, 3.7, 2.3) in 4 region(s); no region is a wall, 4 taper(s) at feature edges (0.02% of surface, budget 2%); 2 more within measurement error of the limit |
| thickness distribution | PASS | median 3.07 mm, p95 10.00 mm, max 22.20 mm |
| hollowable at 1.20 mm wall | WARN | 0.06 of 0.81 cm3 (7%) in 1 pocket(s), 1 too small to shell |
| filament that would save | PASS | 0.01 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.33 mm | (-4.4, 5.7, 7.7) | 6 | 0.1 | 0.6 | 0.17 |
| 2 | taper | 0.13 mm | (-2.9, -3.7, 2.2) | 1 | 0.0 | 0.0 | 0.16 |
| 3 | taper | 0.13 mm | (-2.9, 3.7, 2.3) | 1 | 0.0 | 0.0 | 0.15 |
| 4 | taper | 0.13 mm | (-4.4, -5.7, 7.5) | 1 | 0.0 | 0.0 | 0.14 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.

## Workshop report-format compatibility summary

RESULT: printable at this wall

Manager-added summary of the measured check table above; original CAD-generated text is preserved verbatim. The final verifier returned exit 0. This annotation supplies the legacy summary label required by the proposal validator; it adds no measurement or physical-print claim. Original report SHA256: 6937b69ad9d011e6328766137336664574111ff1488bf430a2c35a5c5dedac1d.
