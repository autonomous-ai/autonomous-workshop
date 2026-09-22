# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_tail_left.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/tail_left/r0001/thickness-tail_left.md`

part_tail_left.step.py: 3.54 cm3 solid, grid 0.133 mm (297x370x38), 144757 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 1.1% of surface below (1373 of 144757 samples); thinnest 0.13 mm at (131.8, 50.1, 3.4) in 14 region(s); 5 wall(s) (widest band 1.93 mm), 9 taper(s) at feature edges (0.05% of surface, budget 2%); 173 more within measurement error of the limit |
| thickness distribution | PASS | median 4.00 mm, p95 24.13 mm, max 45.53 mm |
| hollowable at 1.20 mm wall | WARN | 0.96 of 3.54 cm3 (27%) in 2 pocket(s), 1 too small to shell |
| filament that would save | PASS | 0.14 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.13 mm | (134.1, 44.9, 0.3) | 374 | 8.3 | 7.5 | 1.10 |
| 2 | wall | 0.13 mm | (118.2, 76.7, 2.6) | 371 | 7.5 | 3.9 | 1.93 |
| 3 | wall | 0.13 mm | (130.0, 55.2, 2.5) | 209 | 5.0 | 5.2 | 0.95 |
| 4 | wall | 0.13 mm | (119.6, 63.3, 0.2) | 207 | 4.8 | 3.8 | 1.24 |
| 5 | wall | 0.13 mm | (131.8, 50.1, 3.4) | 133 | 2.7 | 2.0 | 1.34 |
| 6 | taper | 0.13 mm | (125.7, 52.6, -0.0) | 31 | 0.5 | 6.2 | 0.08 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
