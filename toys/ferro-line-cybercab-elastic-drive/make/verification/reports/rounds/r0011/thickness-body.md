# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cybercab/measure/rounds/r0011/parts/body.stl --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cybercab/measure/rounds/r0011/thickness-body.md`

<WORKSHOP_RUN>/artifacts/make/r0001/product/cybercab/measure/rounds/r0011/parts/body.stl: 116.77 cm3 solid, grid 0.410 mm (129x195x444), 355927 surface samples, grid resolved to 0.205 mm, exact where under the minimum

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (grid +/-0.20, exact where under) | PASS | 0.0% of surface below (61 of 355927 samples); thinnest 0.52 mm at (21.7, -32.5, 0.4) in 9 region(s); no region is a wall, 9 taper(s) at feature edges (0.02% of surface, budget 2%); 89 grid reading(s) under the limit measured exact on the mesh |
| thickness distribution | PASS | median 3.28 mm, p95 30.72 mm, max 125.52 mm |
| hollowable at 1.20 mm wall | WARN | 43.34 of 116.77 cm3 (37%) in 2 pocket(s) |
| filament that would save | PASS | 6.50 cm3, 8.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.53 mm | (21.7, 2.6, 0.4) | 16 | 3.1 | 13.0 | 0.24 |
| 2 | taper | 0.54 mm | (21.7, -13.6, 0.4) | 13 | 2.5 | 10.8 | 0.23 |
| 3 | taper | 0.54 mm | (21.7, 34.1, 0.4) | 8 | 1.5 | 7.6 | 0.19 |
| 4 | taper | 0.52 mm | (21.7, -32.5, 0.4) | 6 | 1.2 | 4.2 | 0.28 |
| 5 | taper | 0.53 mm | (21.7, 22.9, 0.4) | 6 | 1.2 | 3.9 | 0.30 |
| 6 | taper | 0.55 mm | (21.7, -8.3, 0.4) | 5 | 1.0 | 2.6 | 0.37 |

Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
