# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_08_rear.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_08_rear/r0001/thickness-body_08_rear.md`

part_body_08_rear.step.py: 0.53 cm3 solid, grid 0.133 mm (107x123x54), 38963 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 3.9% of surface below (1392 of 38963 samples); thinnest 0.13 mm at (3.2, 2.2, 6.5) in 31 region(s); 4 wall(s) (widest band 1.15 mm), 27 taper(s) at feature edges (2.02% of surface, budget 2%) -- OVER BUDGET; 880 more within measurement error of the limit |
| thickness distribution | PASS | median 2.33 mm, p95 6.53 mm, max 13.53 mm |
| hollowable at 1.20 mm wall | PASS | 0.00 of 0.53 cm3 (0%) in 0 pocket(s), 4 too small to shell |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.13 mm | (0.1, 7.5, 1.6) | 209 | 5.1 | 4.4 | 1.15 |
| 2 | taper | 0.13 mm | (3.5, -2.1, 6.5) | 193 | 3.7 | 5.2 | 0.71 |
| 3 | taper | 0.13 mm | (-1.2, 3.6, 6.5) | 189 | 3.6 | 5.2 | 0.69 |
| 4 | taper | 0.13 mm | (-3.8, -1.2, 6.5) | 177 | 3.5 | 5.1 | 0.68 |
| 5 | wall | 0.40 mm | (-6.5, -0.7, 1.2) | 139 | 3.2 | 3.6 | 0.87 |
| 6 | wall | 0.67 mm | (6.5, -0.7, 1.3) | 138 | 3.1 | 3.0 | 1.05 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
