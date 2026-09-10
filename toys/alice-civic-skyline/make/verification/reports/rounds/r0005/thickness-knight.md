# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0005/parts/knight.stl --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0005/thickness-knight.md`

<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0005/parts/knight.stl: 15.62 cm3 solid, grid 0.162 mm (176x176x363), 173168 surface samples, grid resolved to 0.081 mm, exact where under the minimum

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (grid +/-0.08, exact where under) | PASS | 0.1% of surface below (135 of 173168 samples); thinnest 0.31 mm at (-10.0, 5.5, 16.9) in 8 region(s); no region is a wall, 8 taper(s) at feature edges (0.10% of surface, budget 2%); 41 grid reading(s) under the limit measured exact on the mesh |
| thickness distribution | PASS | median 15.64 mm, p95 36.30 mm, max 57.86 mm |
| hollowable at 1.20 mm wall | WARN | 10.53 of 15.62 cm3 (67%) in 1 pocket(s) |
| filament that would save | PASS | 1.58 cm3, 2.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.42 mm | (9.9, -7.8, 17.0) | 95 | 3.4 | 15.6 | 0.22 |
| 2 | taper | 0.48 mm | (-9.8, -7.7, 17.0) | 17 | 0.7 | 2.0 | 0.35 |
| 3 | taper | 0.31 mm | (-10.0, 5.5, 16.9) | 12 | 0.4 | 2.2 | 0.19 |
| 4 | taper | 0.67 mm | (-2.9, 4.5, 57.9) | 3 | 0.1 | 1.2 | 0.07 |
| 5 | taper | 0.70 mm | (-2.9, -4.7, 57.9) | 2 | 0.1 | 0.4 | 0.14 |
| 6 | taper | 0.70 mm | (-2.9, -3.2, 57.9) | 2 | 0.1 | 0.5 | 0.11 |

Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
