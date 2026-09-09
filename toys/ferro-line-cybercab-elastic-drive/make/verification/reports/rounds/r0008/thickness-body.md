# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cybercab/measure/rounds/r0008/parts/body.stl --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cybercab/measure/rounds/r0008/thickness-body.md`

<WORKSHOP_RUN>/artifacts/make/r0001/product/cybercab/measure/rounds/r0008/parts/body.stl: 115.83 cm3 solid, grid 0.410 mm (129x195x444), 353578 surface samples, grid resolved to 0.205 mm, exact where under the minimum

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (grid +/-0.20, exact where under) | FAIL | 0.0% of surface below (57 of 353578 samples); thinnest 0.30 mm at (22.3, 33.6, 0.8) in 10 region(s); 2 wall(s) (widest band 1.65 mm), 3 taper(s) at feature edges and 5 spot(s) too small to be a wall (0.02% of surface, budget 2%); 17 grid reading(s) under the limit measured exact on the mesh |
| thickness distribution | PASS | median 3.28 mm, p95 30.92 mm, max 121.22 mm |
| hollowable at 1.20 mm wall | WARN | 42.95 of 115.83 cm3 (37%) in 3 pocket(s), 1 too small to shell |
| filament that would save | PASS | 6.44 cm3, 8.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.32 mm | (22.2, -17.3, 66.6) | 11 | 2.9 | 1.8 | 1.65 |
| 2 | spot | 0.40 mm | (22.2, -22.7, 66.7) | 8 | 2.1 | 1.3 | 1.66 |
| 3 | taper | 0.30 mm | (22.3, 33.6, 0.8) | 9 | 2.0 | 4.7 | 0.43 |
| 4 | spot | 0.40 mm | (22.2, 16.4, 103.7) | 6 | 1.8 | 1.5 | 1.17 |
| 5 | wall | 0.35 mm | (22.2, -22.4, 103.7) | 6 | 1.7 | 1.7 | 1.00 |
| 6 | spot | 0.35 mm | (22.2, 16.6, 66.7) | 5 | 1.3 | 1.5 | 0.86 |

Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
