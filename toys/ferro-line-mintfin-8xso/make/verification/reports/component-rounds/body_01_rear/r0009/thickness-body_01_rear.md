# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_01_rear.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_01_rear/r0009/thickness-body_01_rear.md`

part_body_01_rear.step.py: 5.61 cm3 solid, grid 0.133 mm (436x329x61), 251994 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.3% of surface below (5602 of 251994 samples); thinnest 0.13 mm at (-4.6, -8.8, 7.5) in 23 region(s); no region is a wall, 23 taper(s) at feature edges (0.34% of surface, budget 2%); 14 more within measurement error of the limit |
| thickness distribution | PASS | median 3.13 mm, p95 17.47 mm, max 57.47 mm |
| hollowable at 1.20 mm wall | WARN | 0.94 of 5.61 cm3 (17%) in 1 pocket(s) |
| filament that would save | PASS | 0.14 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (3.0, -11.9, 7.5) | 1348 | 3.6 | 5.8 | 0.61 |
| 2 | taper | 0.13 mm | (-4.6, -8.8, 7.5) | 1360 | 3.5 | 5.9 | 0.60 |
| 3 | taper | 0.13 mm | (3.5, -5.2, 7.5) | 1406 | 3.5 | 5.8 | 0.59 |
| 4 | taper | 0.13 mm | (-4.5, -7.8, 7.5) | 1428 | 3.4 | 5.8 | 0.59 |
| 5 | taper | 0.73 mm | (0.5, -15.2, 5.7) | 13 | 0.3 | 2.2 | 0.12 |
| 6 | taper | 0.73 mm | (-0.5, -1.4, 3.8) | 8 | 0.2 | 1.1 | 0.15 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
