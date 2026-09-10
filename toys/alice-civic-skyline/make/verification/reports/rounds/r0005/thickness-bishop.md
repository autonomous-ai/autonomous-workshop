# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0005/parts/bishop.stl --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0005/thickness-bishop.md`

<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0005/parts/bishop.stl: 17.08 cm3 solid, grid 0.170 mm (168x168x381), 178808 surface samples, grid resolved to 0.085 mm, exact where under the minimum

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (grid +/-0.09, exact where under) | PASS | 0.6% of surface below (1015 of 178808 samples); thinnest 0.26 mm at (-11.0, 7.9, 14.8) in 4 region(s); no region is a wall, 4 taper(s) at feature edges (0.55% of surface, budget 2%); 490 grid reading(s) under the limit measured exact on the mesh |
| thickness distribution | PASS | median 10.98 mm, p95 59.90 mm, max 63.98 mm |
| hollowable at 1.20 mm wall | WARN | 10.85 of 17.08 cm3 (64%) in 1 pocket(s) |
| filament that would save | PASS | 1.63 cm3, 2.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.36 mm | (10.3, 7.4, 48.4) | 492 | 15.9 | 49.6 | 0.32 |
| 2 | taper | 0.26 mm | (-11.0, 7.9, 14.8) | 450 | 14.4 | 49.1 | 0.29 |
| 3 | taper | 0.38 mm | (-9.8, 7.0, 59.0) | 37 | 1.2 | 2.7 | 0.46 |
| 4 | taper | 0.39 mm | (9.7, 7.2, 57.2) | 36 | 1.2 | 2.7 | 0.45 |

Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
