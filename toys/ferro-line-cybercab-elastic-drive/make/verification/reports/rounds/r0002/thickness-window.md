# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cybercab/measure/rounds/r0002/parts/window.stl --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cybercab/measure/rounds/r0002/thickness-window.md`

<WORKSHOP_RUN>/artifacts/make/r0001/product/cybercab/measure/rounds/r0002/parts/window.stl: 1.08 cm3 solid, grid 0.133 mm (650x125x15), 99601 surface samples, grid resolved to 0.067 mm, exact where under the minimum

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (grid +/-0.07, exact where under) | FAIL | 0.5% of surface below (387 of 99601 samples); thinnest 0.09 mm at (136.8, -39.9, 0.4) in 2 region(s); 2 wall(s) (widest band 2.23 mm); 85 grid reading(s) under the limit measured exact on the mesh |
| thickness distribution | PASS | median 1.33 mm, p95 11.87 mm, max 16.13 mm |
| hollowable at 1.20 mm wall | PASS | 0.00 of 1.08 cm3 (0%) in 0 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.11 mm | (51.2, -41.9, 0.9) | 203 | 4.5 | 2.0 | 2.23 |
| 2 | wall | 0.09 mm | (136.8, -39.9, 0.4) | 184 | 4.0 | 2.0 | 2.01 |

Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
