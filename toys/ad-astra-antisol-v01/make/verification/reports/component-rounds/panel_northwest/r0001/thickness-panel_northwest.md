# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_panel_northwest.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/panel_northwest/r0001/thickness-panel_northwest.md`

part_panel_northwest.step.py: 157.50 cm3 solid, grid 0.277 mm (423x683x37), 379483 surface samples, thickness resolved to 0.139 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.14) | FAIL | 3.8% of surface below (13892 of 379483 samples); thinnest 0.42 mm at (23.4, -93.4, 7.7) in 4 region(s); 4 wall(s) (widest band 16.04 mm); 49 more within measurement error of the limit |
| thickness distribution | PASS | median 8.87 mm, p95 115.87 mm, max 187.94 mm |
| hollowable at 1.20 mm wall | WARN | 102.29 of 157.50 cm3 (65%) in 1 pocket(s) |
| filament that would save | PASS | 15.34 cm3, 19.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.42 mm | (23.4, -93.4, 7.7) | 5615 | 798.5 | 49.8 | 16.04 |
| 2 | wall | 0.42 mm | (-12.5, -93.4, 8.1) | 2781 | 418.5 | 34.3 | 12.22 |
| 3 | wall | 0.55 mm | (57.4, -56.7, 7.7) | 2757 | 412.7 | 34.0 | 12.14 |
| 4 | wall | 0.55 mm | (57.4, 84.4, 4.6) | 2739 | 394.2 | 34.3 | 11.50 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
