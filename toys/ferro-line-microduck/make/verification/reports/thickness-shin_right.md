# Thickness and hollow

`artifacts/make/r0001/product/cad/part_shin_right.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-shin_right.md`

artifacts/make/r0001/product/cad/part_shin_right.stl: 0.39 cm3 solid, grid 0.133 mm (105x109x26), 21837 surface samples, grid resolved to 0.067 mm, exact where under the minimum

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (grid +/-0.07, exact where under) | PASS | 0.0% of surface below (9 of 21837 samples); thinnest 0.59 mm at (31.0, 25.6, 2.3) in 1 region(s); no region is a wall, 1 taper(s) at feature edges (0.04% of surface, budget 2%); 11 grid reading(s) under the limit measured exact on the mesh |
| thickness distribution | PASS | median 2.80 mm, p95 13.53 mm, max 13.93 mm |
| hollowable at 1.20 mm wall | WARN | 0.03 of 0.39 cm3 (9%) in 1 pocket(s) |
| filament that would save | PASS | 0.01 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.59 mm | (31.0, 25.6, 2.3) | 9 | 0.2 | 1.8 | 0.10 |

Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
