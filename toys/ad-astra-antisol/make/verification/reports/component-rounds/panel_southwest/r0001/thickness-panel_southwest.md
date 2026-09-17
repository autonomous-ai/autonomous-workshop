# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_panel_southwest.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/panel_southwest/r0001/thickness-panel_southwest.md`

part_panel_southwest.step.py: 136.75 cm3 solid, grid 0.251 mm (466x609x41), 380828 surface samples, thickness resolved to 0.126 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.13) | FAIL | 3.7% of surface below (13933 of 380828 samples); thinnest 0.50 mm at (57.4, -33.6, 7.0) in 3 region(s); 3 wall(s) (widest band 16.23 mm); 211 more within measurement error of the limit |
| thickness distribution | PASS | median 8.93 mm, p95 115.90 mm, max 151.86 mm |
| hollowable at 1.20 mm wall | WARN | 86.46 of 136.75 cm3 (63%) in 1 pocket(s) |
| filament that would save | PASS | 12.97 cm3, 16.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.50 mm | (58.0, 51.8, 8.6) | 6988 | 805.4 | 49.6 | 16.23 |
| 2 | wall | 0.50 mm | (20.7, 75.3, 8.7) | 3467 | 411.1 | 34.3 | 12.00 |
| 3 | wall | 0.50 mm | (57.4, -33.6, 7.0) | 3478 | 395.1 | 34.1 | 11.59 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
