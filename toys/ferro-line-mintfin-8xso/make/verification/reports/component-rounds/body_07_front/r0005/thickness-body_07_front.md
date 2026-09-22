# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_07_front.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_07_front/r0005/thickness-body_07_front.md`

part_body_07_front.step.py: 0.56 cm3 solid, grid 0.133 mm (150x141x71), 38983 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 12.1% of surface below (4623 of 38983 samples); thinnest 0.13 mm at (4.5, -3.9, 0.2) in 6 region(s); 2 wall(s) (widest band 4.50 mm), 4 taper(s) at feature edges (1.03% of surface, budget 2%); 699 more within measurement error of the limit |
| thickness distribution | PASS | median 1.20 mm, p95 9.00 mm, max 11.27 mm |
| hollowable at 1.20 mm wall | WARN | 0.14 of 0.56 cm3 (25%) in 1 pocket(s) |
| filament that would save | PASS | 0.02 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.13 mm | (4.5, -3.9, 0.2) | 3823 | 72.2 | 16.0 | 4.50 |
| 2 | wall | 0.13 mm | (-1.1, -8.8, 1.0) | 394 | 8.6 | 6.7 | 1.28 |
| 3 | taper | 0.13 mm | (6.1, 3.3, 0.1) | 196 | 3.7 | 4.8 | 0.76 |
| 4 | taper | 0.13 mm | (-5.5, 3.3, 0.1) | 198 | 3.6 | 4.8 | 0.76 |
| 5 | taper | 0.47 mm | (5.6, -7.9, 1.0) | 9 | 0.2 | 1.1 | 0.16 |
| 6 | taper | 0.27 mm | (-7.0, 3.4, 1.2) | 3 | 0.1 | 0.2 | 0.24 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
