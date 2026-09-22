# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_01_rear.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_01_rear/r0010/thickness-body_01_rear.md`

part_body_01_rear.step.py: 5.61 cm3 solid, grid 0.133 mm (436x329x61), 246134 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.4% of surface below (1944 of 246134 samples); thinnest 0.13 mm at (-4.5, -7.8, 7.5) in 17 region(s); no region is a wall, 17 taper(s) at feature edges (0.36% of surface, budget 2%); 80 more within measurement error of the limit |
| thickness distribution | PASS | median 3.13 mm, p95 18.27 mm, max 57.47 mm |
| hollowable at 1.20 mm wall | WARN | 0.94 of 5.61 cm3 (17%) in 1 pocket(s) |
| filament that would save | PASS | 0.14 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (-4.5, -7.8, 7.5) | 485 | 4.0 | 5.8 | 0.69 |
| 2 | taper | 0.20 mm | (-3.6, -10.9, 7.3) | 482 | 3.9 | 5.9 | 0.65 |
| 3 | taper | 0.27 mm | (3.9, -6.2, 7.3) | 467 | 3.7 | 6.0 | 0.62 |
| 4 | taper | 0.13 mm | (4.5, -8.8, 7.5) | 461 | 3.6 | 5.9 | 0.62 |
| 5 | taper | 0.67 mm | (0.6, -1.2, 3.5) | 14 | 0.3 | 3.7 | 0.08 |
| 6 | taper | 0.73 mm | (0.5, -15.2, 6.9) | 11 | 0.2 | 2.2 | 0.10 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
