# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/parts/board_1_1.stl --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/thickness-board_1_1.md`

<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/parts/board_1_1.stl: 146.32 cm3 solid, grid 0.291 mm (664x664x26), 383098 surface samples, grid resolved to 0.146 mm, exact where under the minimum

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (grid +/-0.15, exact where under) | FAIL | 0.0% of surface below (69 of 383098 samples); thinnest 0.21 mm at (1.8, 0.0, 2.5) in 7 region(s); 5 wall(s) (widest band 1.55 mm), 1 taper(s) at feature edges and 1 spot(s) too small to be a wall (0.00% of surface, budget 2%); 41 grid reading(s) under the limit measured exact on the mesh |
| thickness distribution | PASS | median 4.80 mm, p95 41.91 mm, max 191.80 mm |
| hollowable at 1.20 mm wall | WARN | 54.62 of 146.32 cm3 (37%) in 1 pocket(s) |
| filament that would save | PASS | 8.19 cm3, 10.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.21 mm | (1.8, 0.0, 2.5) | 16 | 5.1 | 3.3 | 1.52 |
| 2 | wall | 0.38 mm | (0.0, 85.6, 2.8) | 14 | 3.4 | 2.5 | 1.39 |
| 3 | wall | 0.30 mm | (0.0, 40.3, 4.6) | 10 | 3.1 | 2.0 | 1.55 |
| 4 | wall | 0.35 mm | (85.7, 0.0, 3.9) | 10 | 2.6 | 2.2 | 1.18 |
| 5 | spot | 0.47 mm | (40.3, 0.3, 3.3) | 8 | 2.2 | 1.2 | 1.87 |
| 6 | wall | 0.30 mm | (124.3, 0.0, 4.4) | 7 | 2.0 | 2.0 | 1.01 |

Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
