# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cybercab/measure/rounds/r0003/parts/body.stl --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cybercab/measure/rounds/r0003/thickness-body.md`

<WORKSHOP_RUN>/artifacts/make/r0001/product/cybercab/measure/rounds/r0003/parts/body.stl: 72.99 cm3 solid, grid 0.410 mm (444x195x129), 298408 surface samples, grid resolved to 0.205 mm, exact where under the minimum

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (grid +/-0.20, exact where under) | FAIL | 0.2% of surface below (577 of 298408 samples); thinnest 0.19 mm at (160.8, -35.0, 24.7) in 9 region(s); 3 wall(s) (widest band 1.53 mm), 6 taper(s) at feature edges (0.18% of surface, budget 2%); 270 grid reading(s) under the limit measured exact on the mesh |
| thickness distribution | PASS | median 3.07 mm, p95 15.77 mm, max 98.08 mm |
| hollowable at 1.20 mm wall | WARN | 13.39 of 72.99 cm3 (18%) in 6 pocket(s), 8 too small to shell |
| filament that would save | PASS | 2.01 cm3, 2.5 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.31 mm | (0.6, 31.3, 15.1) | 217 | 51.1 | 72.4 | 0.71 |
| 2 | wall | 0.19 mm | (160.8, -35.0, 24.7) | 67 | 13.7 | 9.0 | 1.53 |
| 3 | taper | 0.19 mm | (179.1, 36.0, 11.1) | 60 | 13.7 | 23.3 | 0.59 |
| 4 | wall | 0.19 mm | (160.8, 33.8, 24.7) | 61 | 12.2 | 8.4 | 1.45 |
| 5 | taper | 0.46 mm | (179.0, -30.1, 11.3) | 50 | 10.8 | 19.3 | 0.56 |
| 6 | taper | 0.45 mm | (179.0, -1.3, 11.3) | 45 | 10.0 | 15.9 | 0.63 |

Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
