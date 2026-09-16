# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_northwest_panel.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/northwest_panel/r0001/thickness-northwest_panel.md`

part_northwest_panel.step.py: 73.05 cm3 solid, grid 0.197 mm (492x797x30), 370358 surface samples, thickness resolved to 0.098 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.10) | FAIL | 1.7% of surface below (2902 of 370358 samples); thinnest 0.20 mm at (80.9, 60.6, 4.6) in 19 region(s); 17 wall(s) (widest band 4.81 mm), 0 taper(s) at feature edges and 2 spot(s) too small to be a wall (0.00% of surface, budget 2%); 406 more within measurement error of the limit |
| thickness distribution | PASS | median 4.92 mm, p95 95.84 mm, max 156.02 mm |
| hollowable at 1.20 mm wall | WARN | 35.20 of 73.05 cm3 (48%) in 1 pocket(s) |
| filament that would save | PASS | 5.28 cm3, 6.5 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.49 mm | (61.6, 29.6, 4.9) | 555 | 111.4 | 23.1 | 4.81 |
| 2 | wall | 0.49 mm | (84.2, 29.6, 4.7) | 551 | 108.6 | 23.0 | 4.71 |
| 3 | wall | 0.20 mm | (80.9, 60.6, 4.6) | 286 | 58.4 | 23.0 | 2.54 |
| 4 | wall | 0.39 mm | (56.8, 59.1, 4.7) | 267 | 54.1 | 23.1 | 2.34 |
| 5 | wall | 0.39 mm | (66.4, 53.0, 4.8) | 286 | 53.1 | 22.0 | 2.42 |
| 6 | wall | 0.39 mm | (66.4, 15.7, 4.7) | 269 | 50.9 | 21.9 | 2.32 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
