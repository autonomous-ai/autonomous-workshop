# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cybercab/measure/rounds/r0002/parts/body.stl --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cybercab/measure/rounds/r0002/thickness-body.md`

<WORKSHOP_RUN>/artifacts/make/r0001/product/cybercab/measure/rounds/r0002/parts/body.stl: 67.65 cm3 solid, grid 0.410 mm (444x195x129), 288787 surface samples, grid resolved to 0.205 mm, exact where under the minimum

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (grid +/-0.20, exact where under) | FAIL | 0.5% of surface below (1213 of 288787 samples); thinnest 0.19 mm at (160.8, -36.8, 24.7) in 6 region(s); 3 wall(s) (widest band 1.37 mm), 3 taper(s) at feature edges (0.17% of surface, budget 2%); 684 grid reading(s) under the limit measured exact on the mesh |
| thickness distribution | PASS | median 3.07 mm, p95 14.33 mm, max 98.08 mm |
| hollowable at 1.20 mm wall | WARN | 11.39 of 67.65 cm3 (17%) in 10 pocket(s), 10 too small to shell |
| filament that would save | PASS | 1.71 cm3, 2.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.19 mm | (160.8, -36.8, 24.7) | 563 | 105.5 | 76.9 | 1.37 |
| 2 | taper | 0.35 mm | (0.6, 34.4, 15.1) | 213 | 49.6 | 72.1 | 0.69 |
| 3 | wall | 0.43 mm | (144.8, 6.0, 29.1) | 208 | 39.9 | 48.3 | 0.83 |
| 4 | taper | 0.23 mm | (179.1, 34.7, 11.2) | 163 | 35.3 | 71.4 | 0.49 |
| 5 | wall | 0.39 mm | (144.8, -36.8, 28.7) | 40 | 8.2 | 8.7 | 0.95 |
| 6 | taper | 0.45 mm | (144.8, 33.5, 29.1) | 26 | 4.9 | 8.2 | 0.60 |

Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
