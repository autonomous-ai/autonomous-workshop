# Thickness and hollow

`artifacts/make/r0001/product/cybercab/part_body.stl --nozzle 0.4 --report artifacts/make/r0001/product/cybercab/measure/thickness-body.md`

artifacts/make/r0001/product/cybercab/part_body.stl: 116.63 cm3 solid, grid 0.410 mm (129x195x444), 355051 surface samples, grid resolved to 0.205 mm, exact where under the minimum

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (grid +/-0.20, exact where under) | PASS | 0.0% of surface below (68 of 355051 samples); thinnest 0.44 mm at (35.7, 35.3, 179.4) in 10 region(s); no region is a wall, 10 taper(s) at feature edges (0.02% of surface, budget 2%); 93 grid reading(s) under the limit measured exact on the mesh |
| thickness distribution | PASS | median 3.28 mm, p95 30.51 mm, max 125.52 mm |
| hollowable at 1.20 mm wall | WARN | 43.34 of 116.63 cm3 (37%) in 2 pocket(s) |
| filament that would save | PASS | 6.50 cm3, 8.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.53 mm | (21.7, -9.2, 0.4) | 18 | 3.5 | 13.3 | 0.26 |
| 2 | taper | 0.53 mm | (21.7, -22.9, 0.4) | 16 | 3.1 | 9.2 | 0.34 |
| 3 | taper | 0.59 mm | (21.8, 21.3, 0.4) | 7 | 1.4 | 4.9 | 0.28 |
| 4 | taper | 0.58 mm | (21.8, -3.9, 0.4) | 6 | 1.2 | 1.8 | 0.64 |
| 5 | taper | 0.55 mm | (21.7, 4.5, 0.4) | 6 | 1.2 | 2.7 | 0.43 |
| 6 | taper | 0.53 mm | (21.7, -36.0, 0.4) | 5 | 1.0 | 1.4 | 0.69 |

Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
