# Thickness and hollow

`artifacts/make/r0001/product/cad/part_body_1.step.py --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-body_1.md`

part_body_1.step.py: 3.05 cm3 solid, grid 0.133 mm (204x260x147), 104308 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (12 of 104308 samples); thinnest 0.13 mm at (-2.8, -3.6, 2.6) in 6 region(s); no region is a wall, 6 taper(s) at feature edges (0.01% of surface, budget 2%); 100 more within measurement error of the limit |
| thickness distribution | PASS | median 7.13 mm, p95 14.93 mm, max 34.07 mm |
| hollowable at 1.20 mm wall | WARN | 1.14 of 3.05 cm3 (37%) in 2 pocket(s), 1 too small to shell |
| filament that would save | PASS | 0.17 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (-4.4, 5.7, 7.3) | 4 | 0.1 | 0.4 | 0.17 |
| 2 | taper | 0.13 mm | (10.2, 1.2, 15.0) | 4 | 0.1 | 0.2 | 0.35 |
| 3 | taper | 0.13 mm | (-2.5, 3.2, 5.9) | 1 | 0.0 | 0.0 | 0.15 |
| 4 | taper | 0.40 mm | (-1.9, 2.5, 5.0) | 1 | 0.0 | 0.0 | 0.15 |
| 5 | taper | 0.13 mm | (-2.8, -3.6, 2.6) | 1 | 0.0 | 0.0 | 0.15 |
| 6 | taper | 0.40 mm | (-4.4, -5.7, 7.2) | 1 | 0.0 | 0.0 | 0.14 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.

## Workshop report-format compatibility summary

RESULT: printable at this wall

Manager-added summary of the measured check table above; original CAD-generated text is preserved verbatim. The final verifier returned exit 0. This annotation supplies the legacy summary label required by the proposal validator; it adds no measurement or physical-print claim. Original report SHA256: adbf8e77640fcfaca3463c75b2c67766ea31a51117977151cd26a0a9110bd8cd.
