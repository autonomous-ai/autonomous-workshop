# Thickness and hollow

`artifacts/make/r0001/product/cad/part_frame.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-frame.md`

artifacts/make/r0001/product/cad/part_frame.stl: 179.67 cm3 solid, grid 0.354 mm (251x507x92), 264459 surface samples, grid resolved to 0.177 mm, exact where under the minimum

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (grid +/-0.18, exact where under) | PASS | 0.0% of surface below (13 of 264459 samples); thinnest 0.21 mm at (23.9, 14.3, 25.0) in 5 region(s); no region is a wall, 4 taper(s) at feature edges and 1 spot(s) too small to be a wall (0.00% of surface, budget 2%); 82 grid reading(s) under the limit measured exact on the mesh |
| thickness distribution | PASS | median 25.83 mm, p95 64.39 mm, max 178.83 mm |
| hollowable at 1.20 mm wall | WARN | 143.00 of 179.67 cm3 (80%) in 1 pocket(s) |
| filament that would save | PASS | 21.45 cm3, 26.6 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.21 mm | (23.9, 14.3, 25.0) | 6 | 0.8 | 4.3 | 0.17 |
| 2 | spot | 0.53 mm | (-8.5, 99.9, 1.0) | 2 | 0.3 | 0.3 | 0.90 |
| 3 | taper | 0.39 mm | (-3.1, 5.6, 23.3) | 2 | 0.3 | 0.4 | 0.63 |
| 4 | taper | 0.38 mm | (28.2, 14.3, 25.0) | 2 | 0.3 | 0.4 | 0.69 |
| 5 | taper | 0.62 mm | (-3.1, 14.4, 22.8) | 1 | 0.1 | 0.0 | 0.35 |

Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
