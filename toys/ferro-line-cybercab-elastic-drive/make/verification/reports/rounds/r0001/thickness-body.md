# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cybercab/measure/rounds/r0001/parts/body.stl --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cybercab/measure/rounds/r0001/thickness-body.md`

<WORKSHOP_RUN>/artifacts/make/r0001/product/cybercab/measure/rounds/r0001/parts/body.stl: 80.03 cm3 solid, grid 0.390 mm (466x205x123), 338188 surface samples, grid resolved to 0.195 mm, exact where under the minimum

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (grid +/-0.20, exact where under) | FAIL | 1.5% of surface below (4789 of 338188 samples); thinnest 0.22 mm at (155.1, 19.7, 21.2) in 12 region(s); 12 wall(s) (widest band 4.99 mm); 1066 grid reading(s) under the limit measured exact on the mesh |
| thickness distribution | PASS | median 3.12 mm, p95 19.70 mm, max 96.73 mm |
| hollowable at 1.20 mm wall | WARN | 19.51 of 80.03 cm3 (24%) in 7 pocket(s) |
| filament that would save | PASS | 2.93 cm3, 3.6 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.22 mm | (155.1, 19.7, 21.2) | 1667 | 257.1 | 77.2 | 3.33 |
| 2 | wall | 0.31 mm | (150.1, 3.1, 22.7) | 978 | 150.6 | 48.9 | 3.08 |
| 3 | wall | 0.50 mm | (67.9, 23.3, 8.0) | 216 | 48.8 | 9.8 | 4.98 |
| 4 | wall | 0.50 mm | (104.6, 18.1, 8.5) | 230 | 48.8 | 9.8 | 4.99 |
| 5 | wall | 0.50 mm | (69.6, -23.1, 8.5) | 231 | 48.2 | 9.7 | 4.94 |
| 6 | wall | 0.50 mm | (71.2, 18.1, 8.5) | 234 | 47.3 | 9.7 | 4.85 |

Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
