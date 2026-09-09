# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cybercab/measure/rounds/r0010/parts/end_wheel.stl --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cybercab/measure/rounds/r0010/thickness-end_wheel.md`

<WORKSHOP_RUN>/artifacts/make/r0001/product/cybercab/measure/rounds/r0010/parts/end_wheel.stl: 5.38 cm3 solid, grid 0.133 mm (252x252x57), 186451 surface samples, grid resolved to 0.067 mm, exact where under the minimum

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (grid +/-0.07, exact where under) | FAIL | 0.9% of surface below (1582 of 186451 samples); thinnest 0.70 mm at (1.7, 1.7, 0.7) in 1 region(s); 1 wall(s) (widest band 5.51 mm); 4 grid reading(s) under the limit measured exact on the mesh |
| thickness distribution | PASS | median 6.93 mm, p95 14.47 mm, max 33.00 mm |
| hollowable at 1.20 mm wall | WARN | 2.14 of 5.38 cm3 (40%) in 1 pocket(s) |
| filament that would save | PASS | 0.32 cm3, 0.4 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.70 mm | (1.7, 1.7, 0.7) | 1582 | 30.3 | 5.5 | 5.51 |

Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
