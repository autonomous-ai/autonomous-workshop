# Thickness and hollow

`artifacts/make/r0001/product/cad/part_boot_left.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-boot_left.md`

artifacts/make/r0001/product/cad/part_boot_left.stl: 2.83 cm3 solid, grid 0.133 mm (252x80x101), 79656 surface samples, grid resolved to 0.067 mm, exact where under the minimum

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (grid +/-0.07, exact where under) | PASS | 1.1% of surface below (737 of 79656 samples); thinnest 0.07 mm at (-25.0, -7.4, 10.4) in 2 region(s); no region is a wall, 2 taper(s) at feature edges (1.11% of surface, budget 2%); 16 grid reading(s) under the limit measured exact on the mesh |
| thickness distribution | PASS | median 9.93 mm, p95 24.00 mm, max 33.47 mm |
| hollowable at 1.20 mm wall | WARN | 1.36 of 2.83 cm3 (48%) in 1 pocket(s) |
| filament that would save | PASS | 0.20 cm3, 0.3 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.07 mm | (-25.0, -7.4, 10.4) | 735 | 16.4 | 23.8 | 0.69 |
| 2 | taper | 0.51 mm | (-3.2, -14.2, 12.8) | 2 | 0.0 | 0.4 | 0.10 |

Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
