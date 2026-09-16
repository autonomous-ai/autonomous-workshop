# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_drive_retainer.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/drive_retainer/r0001/thickness-drive_retainer.md`

part_drive_retainer.step.py: 0.02 cm3 solid, grid 0.133 mm (29x83x12), 3305 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 13.5% of surface below (456 of 3305 samples); thinnest 0.73 mm at (108.6, -3.7, 0.6) in 6 region(s); 3 wall(s) (widest band 1.09 mm), 1 taper(s) at feature edges and 2 spot(s) too small to be a wall (3.74% of surface, budget 2%) -- OVER BUDGET; 476 more within measurement error of the limit |
| thickness distribution | PASS | median 0.93 mm, p95 2.33 mm, max 10.40 mm |
| hollowable at 1.20 mm wall | PASS | 0.00 of 0.02 cm3 (0%) in 0 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.73 mm | (108.6, 0.1, 0.8) | 137 | 3.6 | 3.3 | 1.09 |
| 2 | wall | 0.73 mm | (107.0, 1.2, 0.8) | 133 | 3.4 | 3.6 | 0.94 |
| 3 | spot | 0.73 mm | (108.6, 4.4, 0.8) | 67 | 1.7 | 1.5 | 1.10 |
| 4 | wall | 0.73 mm | (107.0, 4.3, 0.3) | 61 | 1.5 | 1.7 | 0.87 |
| 5 | taper | 0.73 mm | (107.0, -3.6, 0.6) | 30 | 0.8 | 1.0 | 0.77 |
| 6 | spot | 0.73 mm | (108.6, -3.7, 0.6) | 28 | 0.8 | 0.9 | 0.86 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
