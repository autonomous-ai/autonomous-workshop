# Thickness and hollow

`artifacts/make/r0001/product/cad/part_body_6.step.py --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-body_6.md`

part_body_6.step.py: 2.00 cm3 solid, grid 0.133 mm (204x147x125), 74742 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (13 of 74742 samples); thinnest 0.13 mm at (-2.8, 3.7, 0.6) in 6 region(s); no region is a wall, 6 taper(s) at feature edges (0.02% of surface, budget 2%); 82 more within measurement error of the limit |
| thickness distribution | PASS | median 6.87 mm, p95 15.13 mm, max 19.87 mm |
| hollowable at 1.20 mm wall | WARN | 0.65 of 2.00 cm3 (33%) in 2 pocket(s) |
| filament that would save | PASS | 0.10 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.40 mm | (-4.4, 5.7, 7.4) | 3 | 0.1 | 0.5 | 0.10 |
| 2 | taper | 0.60 mm | (-4.4, -5.7, 7.6) | 3 | 0.1 | 0.1 | 0.40 |
| 3 | taper | 0.33 mm | (10.2, 1.2, 12.1) | 3 | 0.1 | 0.1 | 0.40 |
| 4 | taper | 0.20 mm | (10.2, -1.2, 12.1) | 2 | 0.0 | 0.3 | 0.12 |
| 5 | taper | 0.20 mm | (-2.8, 3.6, 6.5) | 1 | 0.0 | 0.0 | 0.15 |
| 6 | taper | 0.13 mm | (-2.8, 3.7, 0.6) | 1 | 0.0 | 0.0 | 0.14 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.

## Workshop report-format compatibility summary

RESULT: printable at this wall

Manager-added summary of the measured check table above; original CAD-generated text is preserved verbatim. The final verifier returned exit 0. This annotation supplies the legacy summary label required by the proposal validator; it adds no measurement or physical-print claim. Original report SHA256: 3274f3bab0e68dddc84a34452a8027d6c0e7b8ea7a40dd155cdea69dc94550cf.
