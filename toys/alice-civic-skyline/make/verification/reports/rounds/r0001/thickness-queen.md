# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/parts/queen.stl --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/thickness-queen.md`

<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/parts/queen.stl: 23.73 cm3 solid, grid 0.188 mm (162x162x410), 170237 surface samples, grid resolved to 0.094 mm, exact where under the minimum

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (grid +/-0.09, exact where under) | FAIL | 0.2% of surface below (244 of 170237 samples); thinnest 0.12 mm at (2.5, 5.7, 62.9) in 2 region(s); 2 wall(s) (widest band 0.99 mm); 12 grid reading(s) under the limit measured exact on the mesh |
| thickness distribution | PASS | median 17.92 mm, p95 54.88 mm, max 75.98 mm |
| hollowable at 1.20 mm wall | WARN | 16.86 of 23.73 cm3 (71%) in 1 pocket(s) |
| filament that would save | PASS | 2.53 cm3, 3.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.12 mm | (2.5, 5.7, 62.9) | 121 | 7.8 | 7.8 | 0.99 |
| 2 | wall | 0.14 mm | (-2.4, -5.7, 63.1) | 123 | 7.1 | 7.8 | 0.91 |

Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
