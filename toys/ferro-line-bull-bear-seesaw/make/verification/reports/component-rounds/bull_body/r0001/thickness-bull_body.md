# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_bull_body.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/bull_body/r0001/thickness-bull_body.md`

part_bull_body.step.py: 38.12 cm3 solid, grid 0.239 mm (330x308x105), 306902 surface samples, thickness resolved to 0.120 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.12) | FAIL | 0.1% of surface below (182 of 306902 samples); thinnest 0.24 mm at (-35.3, -21.4, 7.9) in 5 region(s); 2 wall(s) (widest band 1.31 mm), 3 taper(s) at feature edges (0.01% of surface, budget 2%); 117 more within measurement error of the limit |
| thickness distribution | PASS | median 7.30 mm, p95 27.06 mm, max 81.29 mm |
| hollowable at 1.20 mm wall | WARN | 17.83 of 38.12 cm3 (47%) in 1 pocket(s) |
| filament that would save | PASS | 2.67 cm3, 3.3 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.24 mm | (35.2, -21.5, 10.6) | 86 | 5.1 | 3.9 | 1.31 |
| 2 | wall | 0.24 mm | (-35.3, -21.4, 7.9) | 75 | 4.5 | 3.8 | 1.19 |
| 3 | taper | 0.36 mm | (32.3, 6.2, 4.7) | 12 | 0.9 | 2.5 | 0.38 |
| 4 | taper | 0.36 mm | (-32.3, 6.2, 4.7) | 8 | 0.6 | 2.8 | 0.22 |
| 5 | taper | 0.24 mm | (28.0, 14.2, 5.8) | 1 | 0.1 | 0.0 | 0.22 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
