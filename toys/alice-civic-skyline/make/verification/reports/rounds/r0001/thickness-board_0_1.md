# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/parts/board_0_1.stl --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/thickness-board_0_1.md`

<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/parts/board_0_1.stl: 146.28 cm3 solid, grid 0.291 mm (664x664x26), 382794 surface samples, grid resolved to 0.146 mm, exact where under the minimum

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (grid +/-0.15, exact where under) | FAIL | 0.0% of surface below (70 of 382794 samples); thinnest 0.30 mm at (25.7, 0.0, 4.7) in 8 region(s); 7 wall(s) (widest band 1.40 mm), 0 taper(s) at feature edges and 1 spot(s) too small to be a wall (0.00% of surface, budget 2%); 34 grid reading(s) under the limit measured exact on the mesh |
| thickness distribution | PASS | median 4.80 mm, p95 41.91 mm, max 191.80 mm |
| hollowable at 1.20 mm wall | WARN | 54.69 of 146.28 cm3 (37%) in 1 pocket(s) |
| filament that would save | PASS | 8.20 cm3, 10.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.33 mm | (192.0, 127.7, 4.5) | 11 | 2.8 | 2.3 | 1.22 |
| 2 | wall | 0.32 mm | (64.3, 0.0, 3.5) | 10 | 2.8 | 2.2 | 1.24 |
| 3 | wall | 0.33 mm | (109.7, 0.0, 4.4) | 9 | 2.7 | 1.9 | 1.40 |
| 4 | wall | 0.37 mm | (192.0, 82.4, 3.0) | 10 | 2.7 | 1.9 | 1.37 |
| 5 | wall | 0.30 mm | (25.7, 0.0, 4.7) | 10 | 2.6 | 2.2 | 1.21 |
| 6 | wall | 0.34 mm | (192.0, 166.3, 3.3) | 7 | 2.2 | 2.2 | 0.97 |

Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
