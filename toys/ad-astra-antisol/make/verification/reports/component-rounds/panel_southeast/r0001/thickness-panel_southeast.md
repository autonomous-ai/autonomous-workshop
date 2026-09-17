# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_panel_southeast.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/panel_southeast/r0001/thickness-panel_southeast.md`

part_panel_southeast.step.py: 169.14 cm3 solid, grid 0.277 mm (553x553x37), 380189 surface samples, thickness resolved to 0.139 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.14) | FAIL | 2.9% of surface below (10600 of 380189 samples); thinnest 0.42 mm at (-75.4, -30.4, 8.2) in 4 region(s); 4 wall(s) (widest band 12.11 mm); 40 more within measurement error of the limit |
| thickness distribution | PASS | median 8.87 mm, p95 151.76 mm, max 157.72 mm |
| hollowable at 1.20 mm wall | WARN | 110.47 of 169.14 cm3 (65%) in 1 pocket(s) |
| filament that would save | PASS | 16.57 cm3, 20.5 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.42 mm | (-75.4, -30.4, 8.2) | 2652 | 418.5 | 34.6 | 12.11 |
| 2 | wall | 0.55 mm | (-23.7, 76.0, 8.7) | 2675 | 407.5 | 34.1 | 11.96 |
| 3 | wall | 0.55 mm | (-2.9, 75.3, 4.2) | 2613 | 407.5 | 34.2 | 11.91 |
| 4 | wall | 0.42 mm | (-75.4, -66.4, 7.0) | 2660 | 396.9 | 34.5 | 11.49 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
