# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_01_rear.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_01_rear/r0003/thickness-body_01_rear.md`

part_body_01_rear.step.py: 4.88 cm3 solid, grid 0.133 mm (436x302x61), 224337 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 3.6% of surface below (7569 of 224337 samples); thinnest 0.13 mm at (16.8, -15.4, 2.3) in 18 region(s); 2 wall(s) (widest band 2.41 mm), 16 taper(s) at feature edges (0.39% of surface, budget 2%); 780 more within measurement error of the limit |
| thickness distribution | PASS | median 3.13 mm, p95 14.67 mm, max 57.47 mm |
| hollowable at 1.20 mm wall | WARN | 0.78 of 4.88 cm3 (16%) in 1 pocket(s), 5 too small to shell |
| filament that would save | PASS | 0.12 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.13 mm | (16.8, -15.4, 2.3) | 6218 | 120.4 | 49.9 | 2.41 |
| 2 | wall | 0.13 mm | (1.0, -11.9, 1.0) | 571 | 11.5 | 7.9 | 1.45 |
| 3 | taper | 0.13 mm | (4.4, -9.0, 7.4) | 202 | 4.0 | 5.8 | 0.69 |
| 4 | taper | 0.13 mm | (-2.4, -4.5, 7.4) | 197 | 4.0 | 5.8 | 0.69 |
| 5 | taper | 0.13 mm | (1.6, -4.1, 7.4) | 186 | 3.8 | 5.8 | 0.65 |
| 6 | taper | 0.13 mm | (-4.2, -9.7, 7.4) | 179 | 3.7 | 5.8 | 0.64 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
