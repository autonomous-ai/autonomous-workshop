# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_01_rear.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_01_rear/r0005/thickness-body_01_rear.md`

part_body_01_rear.step.py: 5.61 cm3 solid, grid 0.133 mm (436x329x61), 243182 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.4% of surface below (829 of 243182 samples); thinnest 0.13 mm at (4.4, -7.5, 7.4) in 20 region(s); no region is a wall, 20 taper(s) at feature edges (0.38% of surface, budget 2%); 120 more within measurement error of the limit |
| thickness distribution | PASS | median 3.13 mm, p95 18.53 mm, max 57.47 mm |
| hollowable at 1.20 mm wall | WARN | 0.94 of 5.61 cm3 (17%) in 1 pocket(s) |
| filament that would save | PASS | 0.14 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (4.4, -7.5, 7.4) | 216 | 4.4 | 5.7 | 0.76 |
| 2 | taper | 0.13 mm | (4.0, -10.3, 7.4) | 200 | 4.0 | 5.7 | 0.70 |
| 3 | taper | 0.13 mm | (-4.0, -10.3, 7.4) | 190 | 4.0 | 5.7 | 0.70 |
| 4 | taper | 0.13 mm | (-0.7, -3.9, 7.4) | 178 | 3.7 | 5.8 | 0.64 |
| 5 | taper | 0.67 mm | (0.6, -1.2, 3.7) | 15 | 0.3 | 4.0 | 0.08 |
| 6 | taper | 0.73 mm | (0.5, -15.2, 3.8) | 4 | 0.1 | 0.7 | 0.12 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
