# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_01_rear.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_01_rear/r0008/thickness-body_01_rear.md`

part_body_01_rear.step.py: 5.61 cm3 solid, grid 0.133 mm (436x329x61), 256315 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.3% of surface below (9094 of 256315 samples); thinnest 0.13 mm at (4.5, -8.8, 7.5) in 21 region(s); no region is a wall, 21 taper(s) at feature edges (0.29% of surface, budget 2%); 6 more within measurement error of the limit |
| thickness distribution | PASS | median 3.13 mm, p95 16.95 mm, max 57.47 mm |
| hollowable at 1.20 mm wall | WARN | 0.94 of 5.61 cm3 (17%) in 1 pocket(s) |
| filament that would save | PASS | 0.14 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (4.5, -8.8, 7.5) | 2162 | 3.0 | 5.8 | 0.51 |
| 2 | taper | 0.13 mm | (3.3, -5.0, 7.4) | 2118 | 3.0 | 6.0 | 0.49 |
| 3 | taper | 0.13 mm | (-4.5, -7.8, 7.5) | 2370 | 2.9 | 5.9 | 0.50 |
| 4 | taper | 0.20 mm | (-4.1, -10.0, 7.3) | 2396 | 2.9 | 6.0 | 0.49 |
| 5 | taper | 0.73 mm | (0.5, -15.3, 7.4) | 12 | 0.2 | 2.9 | 0.09 |
| 6 | taper | 0.73 mm | (0.5, -1.4, 3.5) | 8 | 0.2 | 2.5 | 0.06 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
