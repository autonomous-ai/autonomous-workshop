# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/parts/knight.stl --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/thickness-knight.md`

<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/parts/knight.stl: 15.57 cm3 solid, grid 0.162 mm (176x176x363), 172871 surface samples, grid resolved to 0.081 mm, exact where under the minimum

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (grid +/-0.08, exact where under) | PASS | 0.0% of surface below (9 of 172871 samples); thinnest 0.67 mm at (-2.9, -4.4, 57.9) in 4 region(s); no region is a wall, 4 taper(s) at feature edges (0.01% of surface, budget 2%); 13 grid reading(s) under the limit measured exact on the mesh |
| thickness distribution | PASS | median 15.96 mm, p95 35.74 mm, max 57.86 mm |
| hollowable at 1.20 mm wall | WARN | 10.49 of 15.57 cm3 (67%) in 1 pocket(s) |
| filament that would save | PASS | 1.57 cm3, 2.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.67 mm | (-2.9, -4.4, 57.9) | 5 | 0.1 | 2.3 | 0.07 |
| 2 | taper | 0.72 mm | (-2.9, 4.0, 57.9) | 2 | 0.1 | 0.1 | 0.37 |
| 3 | taper | 0.71 mm | (-2.9, 1.1, 57.9) | 1 | 0.0 | 0.0 | 0.18 |
| 4 | taper | 0.73 mm | (-2.9, 3.3, 57.9) | 1 | 0.0 | 0.0 | 0.18 |

Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
