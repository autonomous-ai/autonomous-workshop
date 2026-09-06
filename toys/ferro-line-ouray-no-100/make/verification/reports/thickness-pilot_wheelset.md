# Thickness and hollow

`artifacts/make/r0001/product/cad-project/part_pilot_wheelset.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad-project/measure/thickness-pilot_wheelset.md`

artifacts/make/r0001/product/cad-project/part_pilot_wheelset.stl: 0.28 cm3 solid, grid 0.133 mm (57x170x57), 20491 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (2 of 20491 samples); thinnest 0.27 mm at (22.4, -6.3, 5.3) in 2 region(s); no region is a wall, 2 taper(s) at feature edges (0.01% of surface, budget 2%) |
| thickness distribution | PASS | median 2.93 mm, p95 7.00 mm, max 22.00 mm |
| hollowable at 1.20 mm wall | WARN | 0.01 of 0.28 cm3 (2%) in 1 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.27 mm | (22.4, -6.3, 5.3) | 1 | 0.0 | 0.0 | 0.25 |
| 2 | taper | 0.67 mm | (21.4, -6.3, 2.7) | 1 | 0.0 | 0.0 | 0.22 |

Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
