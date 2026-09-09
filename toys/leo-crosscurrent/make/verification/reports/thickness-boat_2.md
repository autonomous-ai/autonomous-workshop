# Thickness and hollow

`artifacts/make/r0001/product/cad/part_boat_2.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-boat_2.md`

artifacts/make/r0001/product/cad/part_boat_2.stl: 0.88 cm3 solid, grid 0.133 mm (155x155x44), 51077 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (5 of 51077 samples); thinnest 0.73 mm at (6.0, 7.0, 2.4) in 5 region(s); no region is a wall, 5 taper(s) at feature edges (0.01% of surface, budget 2%); 39 more within measurement error of the limit |
| thickness distribution | PASS | median 2.93 mm, p95 16.27 mm, max 16.47 mm |
| hollowable at 1.20 mm wall | WARN | 0.07 of 0.88 cm3 (8%) in 1 pocket(s) |
| filament that would save | PASS | 0.01 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.73 mm | (6.0, 7.0, 2.4) | 1 | 0.0 | 0.0 | 0.13 |
| 2 | taper | 0.73 mm | (3.0, 8.8, 2.4) | 1 | 0.0 | 0.0 | 0.13 |
| 3 | taper | 0.73 mm | (3.3, -8.7, 2.4) | 1 | 0.0 | 0.0 | 0.13 |
| 4 | taper | 0.73 mm | (0.8, -9.2, 2.4) | 1 | 0.0 | 0.0 | 0.13 |
| 5 | taper | 0.73 mm | (-9.2, -0.8, 2.4) | 1 | 0.0 | 0.0 | 0.13 |

Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
