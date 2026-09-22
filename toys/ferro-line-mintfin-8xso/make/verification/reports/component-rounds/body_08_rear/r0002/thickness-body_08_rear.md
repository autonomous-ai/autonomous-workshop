# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_08_rear.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_08_rear/r0002/thickness-body_08_rear.md`

part_body_08_rear.step.py: 0.38 cm3 solid, grid 0.133 mm (107x108x43), 30175 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 2.5% of surface below (762 of 30175 samples); thinnest 0.13 mm at (3.1, -3.3, 1.8) in 16 region(s); no region is a wall, 16 taper(s) at feature edges (2.47% of surface, budget 2%) -- OVER BUDGET; 47 more within measurement error of the limit |
| thickness distribution | PASS | median 2.33 mm, p95 5.07 mm, max 5.07 mm |
| hollowable at 1.20 mm wall | PASS | 0.00 of 0.38 cm3 (0%) in 0 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (-1.2, -4.0, 5.0) | 185 | 3.8 | 5.1 | 0.74 |
| 2 | taper | 0.13 mm | (3.7, -1.4, 5.0) | 187 | 3.7 | 5.1 | 0.72 |
| 3 | taper | 0.13 mm | (3.7, 1.1, 5.0) | 191 | 3.6 | 5.2 | 0.69 |
| 4 | taper | 0.13 mm | (-1.2, 3.5, 5.0) | 177 | 3.3 | 5.1 | 0.63 |
| 5 | taper | 0.47 mm | (6.6, -0.8, 2.1) | 5 | 0.1 | 1.2 | 0.07 |
| 6 | taper | 0.40 mm | (-3.4, -3.0, 3.4) | 2 | 0.1 | 0.8 | 0.10 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
