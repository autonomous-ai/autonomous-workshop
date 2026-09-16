# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_northeast_panel.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/northeast_panel/r0001/thickness-northeast_panel.md`

part_northeast_panel.step.py: 97.05 cm3 solid, grid 0.217 mm (585x723x28), 367256 surface samples, thickness resolved to 0.109 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.11) | FAIL | 2.0% of surface below (3258 of 367256 samples); thinnest 0.22 mm at (29.3, 147.1, 4.7) in 33 region(s); 27 wall(s) (widest band 6.02 mm), 1 taper(s) at feature edges and 5 spot(s) too small to be a wall (0.02% of surface, budget 2%); 102 more within measurement error of the limit |
| thickness distribution | PASS | median 5.00 mm, p95 125.86 mm, max 155.94 mm |
| hollowable at 1.20 mm wall | WARN | 43.17 of 97.05 cm3 (44%) in 1 pocket(s) |
| filament that would save | PASS | 6.48 cm3, 8.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.22 mm | (29.3, 147.1, 4.7) | 998 | 270.1 | 44.8 | 6.02 |
| 2 | wall | 0.33 mm | (54.7, 30.9, 4.8) | 376 | 108.4 | 23.0 | 4.72 |
| 3 | wall | 0.33 mm | (74.8, 30.9, 4.6) | 386 | 107.7 | 22.9 | 4.71 |
| 4 | wall | 0.22 mm | (45.4, 60.4, 4.6) | 200 | 59.0 | 23.1 | 2.55 |
| 5 | wall | 0.43 mm | (82.7, 59.1, 4.8) | 206 | 53.7 | 22.6 | 2.37 |
| 6 | wall | 0.43 mm | (59.1, 4.5, 4.7) | 190 | 51.6 | 21.9 | 2.35 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
