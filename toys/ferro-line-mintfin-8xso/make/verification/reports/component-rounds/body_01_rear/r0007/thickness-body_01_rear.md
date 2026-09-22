# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_01_rear.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_01_rear/r0007/thickness-body_01_rear.md`

part_body_01_rear.step.py: 5.61 cm3 solid, grid 0.133 mm (436x329x61), 246116 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (53 of 246116 samples); thinnest 0.13 mm at (-3.0, -4.5, 4.2) in 20 region(s); no region is a wall, 20 taper(s) at feature edges (0.02% of surface, budget 2%); 3 more within measurement error of the limit |
| thickness distribution | PASS | median 3.13 mm, p95 18.40 mm, max 57.47 mm |
| hollowable at 1.20 mm wall | WARN | 0.94 of 5.61 cm3 (17%) in 1 pocket(s) |
| filament that would save | PASS | 0.14 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.47 mm | (0.6, -15.4, 3.3) | 7 | 0.1 | 1.2 | 0.12 |
| 2 | taper | 0.73 mm | (0.5, -1.3, 7.4) | 5 | 0.1 | 1.4 | 0.07 |
| 3 | taper | 0.73 mm | (-0.5, -1.4, 3.9) | 5 | 0.1 | 1.5 | 0.07 |
| 4 | taper | 0.27 mm | (7.1, -7.7, 3.4) | 5 | 0.1 | 0.5 | 0.19 |
| 5 | taper | 0.73 mm | (0.5, -15.3, 5.4) | 4 | 0.1 | 0.3 | 0.30 |
| 6 | taper | 0.47 mm | (-7.1, -7.7, 3.5) | 4 | 0.1 | 0.3 | 0.32 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
