# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/parts/board_1_0.stl --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/thickness-board_1_0.md`

<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/parts/board_1_0.stl: 146.27 cm3 solid, grid 0.291 mm (664x664x26), 384408 surface samples, grid resolved to 0.146 mm, exact where under the minimum

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (grid +/-0.15, exact where under) | FAIL | 0.0% of surface below (61 of 384408 samples); thinnest 0.29 mm at (82.3, 192.0, 3.4) in 8 region(s); 7 wall(s) (widest band 1.46 mm), 0 taper(s) at feature edges and 1 spot(s) too small to be a wall (0.00% of surface, budget 2%); 31 grid reading(s) under the limit measured exact on the mesh |
| thickness distribution | PASS | median 4.80 mm, p95 41.91 mm, max 191.80 mm |
| hollowable at 1.20 mm wall | WARN | 54.73 of 146.27 cm3 (37%) in 1 pocket(s) |
| filament that would save | PASS | 8.21 cm3, 10.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.36 mm | (0.0, 25.6, 4.7) | 11 | 2.9 | 2.0 | 1.46 |
| 2 | wall | 0.29 mm | (82.3, 192.0, 3.4) | 11 | 2.8 | 1.9 | 1.46 |
| 3 | wall | 0.31 mm | (0.0, 64.3, 2.6) | 10 | 2.6 | 2.3 | 1.11 |
| 4 | wall | 0.34 mm | (166.3, 192.0, 4.4) | 7 | 2.0 | 2.1 | 0.93 |
| 5 | spot | 0.36 mm | (0.0, 148.4, 3.3) | 6 | 1.7 | 1.2 | 1.45 |
| 6 | wall | 0.46 mm | (0.3, 109.7, 3.9) | 5 | 1.6 | 1.7 | 0.93 |

Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
