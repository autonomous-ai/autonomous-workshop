# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_01_rear.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_01_rear/r0001/thickness-body_01_rear.md`

part_body_01_rear.step.py: 5.69 cm3 solid, grid 0.133 mm (436x337x61), 250527 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 1.5% of surface below (3635 of 250527 samples); thinnest 0.13 mm at (-3.8, -5.1, 5.7) in 30 region(s); 3 wall(s) (widest band 4.36 mm), 27 taper(s) at feature edges (0.42% of surface, budget 2%); 420 more within measurement error of the limit |
| thickness distribution | PASS | median 3.13 mm, p95 13.87 mm, max 57.47 mm |
| hollowable at 1.20 mm wall | WARN | 0.95 of 5.69 cm3 (17%) in 1 pocket(s) |
| filament that would save | PASS | 0.14 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.13 mm | (-2.0, -7.9, 0.2) | 2105 | 37.0 | 8.5 | 4.36 |
| 2 | wall | 0.13 mm | (1.2, -21.7, 1.6) | 395 | 7.3 | 4.2 | 1.72 |
| 3 | taper | 0.13 mm | (-3.8, -10.6, 7.4) | 211 | 4.3 | 5.7 | 0.75 |
| 4 | taper | 0.13 mm | (-4.4, -7.6, 7.4) | 188 | 3.8 | 5.8 | 0.67 |
| 5 | taper | 0.13 mm | (3.8, -5.9, 7.4) | 186 | 3.8 | 5.7 | 0.67 |
| 6 | taper | 0.13 mm | (4.1, -10.1, 7.4) | 182 | 3.6 | 5.7 | 0.63 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
