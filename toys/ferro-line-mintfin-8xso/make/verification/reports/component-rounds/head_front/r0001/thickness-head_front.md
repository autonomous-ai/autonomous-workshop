# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_head_front.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/head_front/r0001/thickness-head_front.md`

part_head_front.step.py: 51.45 cm3 solid, grid 0.207 mm (327x227x142), 217901 surface samples, thickness resolved to 0.103 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.10) | FAIL | 0.5% of surface below (867 of 217901 samples); thinnest 0.21 mm at (12.6, 17.8, 21.0) in 40 region(s); 2 wall(s) (widest band 1.34 mm), 38 taper(s) at feature edges (0.02% of surface, budget 2%); 391 more within measurement error of the limit |
| thickness distribution | PASS | median 24.61 mm, p95 59.26 mm, max 66.50 mm |
| hollowable at 1.20 mm wall | WARN | 40.43 of 51.45 cm3 (79%) in 1 pocket(s) |
| filament that would save | PASS | 6.06 cm3, 7.5 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.21 mm | (-8.3, 16.6, 24.5) | 420 | 22.1 | 16.4 | 1.34 |
| 2 | wall | 0.21 mm | (12.6, 17.8, 21.0) | 404 | 20.6 | 16.6 | 1.24 |
| 3 | taper | 0.31 mm | (-27.6, -10.3, 26.5) | 3 | 0.1 | 1.3 | 0.11 |
| 4 | taper | 0.62 mm | (1.0, -18.5, 28.2) | 2 | 0.1 | 0.0 | 0.62 |
| 5 | taper | 0.21 mm | (-27.8, 11.3, 21.9) | 2 | 0.1 | 0.8 | 0.12 |
| 6 | taper | 0.21 mm | (22.3, 18.8, 15.9) | 2 | 0.1 | 1.3 | 0.06 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
