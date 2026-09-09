# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cybercab/measure/rounds/r0004/parts/chassis.stl --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cybercab/measure/rounds/r0004/thickness-chassis.md`

<WORKSHOP_RUN>/artifacts/make/r0001/product/cybercab/measure/rounds/r0004/parts/chassis.stl: 30.04 cm3 solid, grid 0.251 mm (665x239x69), 341839 surface samples, grid resolved to 0.126 mm, exact where under the minimum

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (grid +/-0.13, exact where under) | FAIL | 0.0% of surface below (56 of 341839 samples); thinnest 0.21 mm at (103.1, 13.1, 6.4) in 1 region(s); 1 wall(s) (widest band 0.98 mm); 27 grid reading(s) under the limit measured exact on the mesh |
| thickness distribution | PASS | median 3.02 mm, p95 22.88 mm, max 165.94 mm |
| hollowable at 1.20 mm wall | WARN | 4.58 of 30.04 cm3 (15%) in 1 pocket(s) |
| filament that would save | PASS | 0.69 cm3, 0.9 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.21 mm | (103.1, 13.1, 6.4) | 56 | 4.3 | 4.4 | 0.98 |

Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
