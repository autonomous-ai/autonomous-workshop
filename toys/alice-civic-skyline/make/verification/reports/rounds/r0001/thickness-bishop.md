# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/parts/bishop.stl --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/thickness-bishop.md`

<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/parts/bishop.stl: 12.95 cm3 solid, grid 0.170 mm (168x168x381), 159057 surface samples, grid resolved to 0.085 mm, exact where under the minimum

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (grid +/-0.09, exact where under) | PASS | 1.7% of surface below (2764 of 159057 samples); thinnest 0.11 mm at (-9.3, -7.5, 16.4) in 6 region(s); no region is a wall, 6 taper(s) at feature edges (1.70% of surface, budget 2%); 826 grid reading(s) under the limit measured exact on the mesh |
| thickness distribution | PASS | median 9.02 mm, p95 52.92 mm, max 63.98 mm |
| hollowable at 1.20 mm wall | WARN | 7.67 of 12.95 cm3 (59%) in 1 pocket(s) |
| filament that would save | PASS | 1.15 cm3, 1.4 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.11 mm | (-9.3, -7.5, 16.4) | 1032 | 32.7 | 44.7 | 0.73 |
| 2 | taper | 0.27 mm | (1.8, 9.3, 41.5) | 915 | 27.6 | 43.7 | 0.63 |
| 3 | taper | 0.21 mm | (9.3, -7.5, 16.2) | 504 | 16.0 | 44.4 | 0.36 |
| 4 | taper | 0.25 mm | (1.5, 7.9, 59.0) | 127 | 3.8 | 5.8 | 0.66 |
| 5 | taper | 0.27 mm | (-7.8, -6.4, 53.5) | 123 | 3.8 | 5.8 | 0.65 |
| 6 | taper | 0.39 mm | (7.9, -6.2, 58.4) | 63 | 1.9 | 5.9 | 0.33 |

Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
