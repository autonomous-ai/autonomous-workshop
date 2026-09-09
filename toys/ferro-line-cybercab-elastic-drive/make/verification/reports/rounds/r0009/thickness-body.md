# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cybercab/measure/rounds/r0009/parts/body.stl --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cybercab/measure/rounds/r0009/thickness-body.md`

<WORKSHOP_RUN>/artifacts/make/r0001/product/cybercab/measure/rounds/r0009/parts/body.stl: 116.90 cm3 solid, grid 0.410 mm (129x195x444), 357877 surface samples, grid resolved to 0.205 mm, exact where under the minimum

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (grid +/-0.20, exact where under) | FAIL | 0.0% of surface below (104 of 357877 samples); thinnest 0.29 mm at (9.0, 38.2, 167.6) in 16 region(s); 1 wall(s) (widest band 1.30 mm), 9 taper(s) at feature edges and 6 spot(s) too small to be a wall (0.03% of surface, budget 2%); 125 grid reading(s) under the limit measured exact on the mesh |
| thickness distribution | PASS | median 3.28 mm, p95 30.51 mm, max 125.52 mm |
| hollowable at 1.20 mm wall | WARN | 43.14 of 116.90 cm3 (37%) in 2 pocket(s), 2 too small to shell |
| filament that would save | PASS | 6.47 cm3, 8.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | spot | 0.45 mm | (9.0, -37.4, 167.8) | 12 | 3.4 | 1.6 | 2.18 |
| 2 | taper | 0.53 mm | (21.7, 27.9, 0.4) | 13 | 2.5 | 11.2 | 0.23 |
| 3 | wall | 0.39 mm | (9.0, 38.8, 53.7) | 9 | 2.1 | 1.6 | 1.30 |
| 4 | spot | 0.29 mm | (9.0, 38.2, 167.6) | 7 | 2.1 | 1.4 | 1.43 |
| 5 | taper | 0.54 mm | (21.7, -15.1, 0.4) | 10 | 1.9 | 7.2 | 0.27 |
| 6 | spot | 0.45 mm | (14.7, -37.2, 175.9) | 6 | 1.8 | 1.4 | 1.30 |

Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
