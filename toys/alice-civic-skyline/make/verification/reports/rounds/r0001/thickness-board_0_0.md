# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/parts/board_0_0.stl --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/thickness-board_0_0.md`

<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/parts/board_0_0.stl: 146.63 cm3 solid, grid 0.291 mm (664x664x26), 383060 surface samples, grid resolved to 0.146 mm, exact where under the minimum

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (grid +/-0.15, exact where under) | FAIL | 0.0% of surface below (56 of 383060 samples); thinnest 0.33 mm at (192.0, 106.3, 3.2) in 7 region(s); 4 wall(s) (widest band 1.27 mm), 0 taper(s) at feature edges and 3 spot(s) too small to be a wall (0.01% of surface, budget 2%); 30 grid reading(s) under the limit measured exact on the mesh |
| thickness distribution | PASS | median 4.80 mm, p95 41.91 mm, max 191.80 mm |
| hollowable at 1.20 mm wall | WARN | 54.83 of 146.63 cm3 (37%) in 1 pocket(s) |
| filament that would save | PASS | 8.22 cm3, 10.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.42 mm | (192.0, 190.4, 3.8) | 11 | 3.9 | 3.2 | 1.22 |
| 2 | wall | 0.39 mm | (67.6, 192.0, 3.5) | 9 | 2.5 | 1.9 | 1.27 |
| 3 | wall | 0.34 mm | (192.0, 151.7, 2.6) | 9 | 2.4 | 2.0 | 1.22 |
| 4 | spot | 0.36 mm | (151.6, 192.0, 3.5) | 7 | 2.2 | 0.8 | 2.57 |
| 5 | wall | 0.33 mm | (192.0, 106.3, 3.2) | 9 | 2.1 | 1.9 | 1.09 |
| 6 | spot | 0.39 mm | (192.0, 67.6, 3.4) | 6 | 1.7 | 1.4 | 1.27 |

Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
