# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cybercab/measure/rounds/r0010/parts/body.stl --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cybercab/measure/rounds/r0010/thickness-body.md`

<WORKSHOP_RUN>/artifacts/make/r0001/product/cybercab/measure/rounds/r0010/parts/body.stl: 116.60 cm3 solid, grid 0.410 mm (129x195x444), 355961 surface samples, grid resolved to 0.205 mm, exact where under the minimum

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (grid +/-0.20, exact where under) | PASS | 0.0% of surface below (54 of 355961 samples); thinnest 0.53 mm at (21.7, 0.4, 0.4) in 10 region(s); no region is a wall, 10 taper(s) at feature edges (0.02% of surface, budget 2%); 82 grid reading(s) under the limit measured exact on the mesh |
| thickness distribution | PASS | median 3.28 mm, p95 30.51 mm, max 125.52 mm |
| hollowable at 1.20 mm wall | WARN | 43.17 of 116.60 cm3 (37%) in 2 pocket(s) |
| filament that would save | PASS | 6.48 cm3, 8.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.53 mm | (21.7, -22.5, 0.4) | 15 | 2.9 | 15.9 | 0.18 |
| 2 | taper | 0.53 mm | (21.7, 0.4, 0.4) | 9 | 1.7 | 4.4 | 0.40 |
| 3 | taper | 0.55 mm | (21.7, 25.5, 0.4) | 8 | 1.5 | 6.6 | 0.23 |
| 4 | taper | 0.53 mm | (21.7, 7.1, 0.4) | 6 | 1.2 | 4.3 | 0.27 |
| 5 | taper | 0.57 mm | (21.7, 17.3, 0.4) | 6 | 1.2 | 7.3 | 0.16 |
| 6 | taper | 0.53 mm | (21.7, -7.8, 0.4) | 4 | 0.8 | 3.6 | 0.21 |

Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
