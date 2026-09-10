# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0003/parts/bishop.stl --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0003/thickness-bishop.md`

<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0003/parts/bishop.stl: 14.00 cm3 solid, grid 0.188 mm (152x152x490), 135641 surface samples, grid resolved to 0.094 mm, exact where under the minimum

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (grid +/-0.09, exact where under) | PASS | 0.4% of surface below (530 of 135641 samples); thinnest 0.09 mm at (11.0, 8.0, 7.7) in 8 region(s); no region is a wall, 8 taper(s) at feature edges (0.43% of surface, budget 2%); 55 grid reading(s) under the limit measured exact on the mesh |
| thickness distribution | PASS | median 10.69 mm, p95 40.90 mm, max 40.90 mm |
| hollowable at 1.20 mm wall | WARN | 8.70 of 14.00 cm3 (62%) in 3 pocket(s) |
| filament that would save | PASS | 1.31 cm3, 1.6 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.42 mm | (10.2, 7.5, -21.0) | 159 | 5.8 | 26.2 | 0.22 |
| 2 | taper | 0.42 mm | (-10.3, 7.3, -14.8) | 135 | 4.9 | 20.8 | 0.24 |
| 3 | taper | 0.09 mm | (11.0, 8.0, 7.7) | 67 | 3.7 | 10.1 | 0.37 |
| 4 | taper | 0.19 mm | (-10.9, 8.0, 7.8) | 65 | 3.4 | 10.1 | 0.34 |
| 5 | taper | 0.42 mm | (11.4, 8.1, 51.4) | 38 | 1.6 | 5.3 | 0.30 |
| 6 | taper | 0.42 mm | (-11.4, 8.1, 53.4) | 26 | 1.1 | 2.7 | 0.39 |

Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
