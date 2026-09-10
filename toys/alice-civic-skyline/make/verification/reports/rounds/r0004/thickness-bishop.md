# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0004/parts/bishop.stl --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0004/thickness-bishop.md`

<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0004/parts/bishop.stl: 16.98 cm3 solid, grid 0.170 mm (168x168x381), 177119 surface samples, grid resolved to 0.085 mm, exact where under the minimum

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (grid +/-0.09, exact where under) | PASS | 0.6% of surface below (1057 of 177119 samples); thinnest 0.30 mm at (10.9, 8.0, 14.8) in 7 region(s); no region is a wall, 6 taper(s) at feature edges and 1 spot(s) too small to be a wall (0.58% of surface, budget 2%); 567 grid reading(s) under the limit measured exact on the mesh |
| thickness distribution | PASS | median 10.72 mm, p95 59.90 mm, max 63.98 mm |
| hollowable at 1.20 mm wall | WARN | 10.75 of 16.98 cm3 (63%) in 1 pocket(s) |
| filament that would save | PASS | 1.61 cm3, 2.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.36 mm | (-10.3, 7.4, 37.6) | 473 | 15.4 | 48.7 | 0.32 |
| 2 | taper | 0.30 mm | (10.9, 8.0, 14.8) | 421 | 14.0 | 41.0 | 0.34 |
| 3 | taper | 0.38 mm | (10.8, 8.0, 9.3) | 53 | 1.8 | 4.1 | 0.43 |
| 4 | taper | 0.38 mm | (11.3, 8.3, 54.5) | 38 | 1.3 | 2.7 | 0.46 |
| 5 | taper | 0.40 mm | (-9.8, 7.0, 57.9) | 36 | 1.2 | 2.6 | 0.46 |
| 6 | taper | 0.39 mm | (9.7, 7.2, 59.5) | 33 | 1.1 | 2.5 | 0.44 |

Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
