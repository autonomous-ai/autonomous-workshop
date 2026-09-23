# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_bull_body.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/bull_body/r0010/thickness-bull_body.md`

part_bull_body.step.py: 28.63 cm3 solid, grid 0.291 mm (369x286x105), 166819 surface samples, thickness resolved to 0.146 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.15) | PASS | 0.1% of surface below (96 of 166819 samples); thinnest 0.29 mm at (-12.6, 37.2, 24.9) in 6 region(s); no region is a wall, 6 taper(s) at feature edges (0.07% of surface, budget 2%); 35 more within measurement error of the limit |
| thickness distribution | PASS | median 4.37 mm, p95 28.38 mm, max 85.13 mm |
| hollowable at 1.20 mm wall | WARN | 12.50 of 28.63 cm3 (44%) in 1 pocket(s) |
| filament that would save | PASS | 1.88 cm3, 2.3 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.29 mm | (-11.0, -16.0, 3.1) | 39 | 4.1 | 5.4 | 0.75 |
| 2 | taper | 0.29 mm | (11.0, -15.1, 1.1) | 24 | 3.1 | 5.0 | 0.62 |
| 3 | taper | 0.29 mm | (-9.5, 28.7, 25.0) | 13 | 1.4 | 2.1 | 0.68 |
| 4 | taper | 0.29 mm | (-9.4, 37.2, 26.9) | 11 | 1.0 | 2.6 | 0.39 |
| 5 | taper | 0.44 mm | (-12.6, 28.8, 24.8) | 5 | 0.4 | 1.6 | 0.27 |
| 6 | taper | 0.29 mm | (-12.6, 37.2, 24.9) | 4 | 0.3 | 1.4 | 0.24 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
