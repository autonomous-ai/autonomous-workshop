# Thickness and hollow

`artifacts/make/r0001/product/cad-project/part_tender_wheelset_3.stl --nozzle 0.4 --report artifacts/make/r0001/product/cad-project/measure/thickness-tender_wheelset_3.md`

artifacts/make/r0001/product/cad-project/part_tender_wheelset_3.stl: 0.32 cm3 solid, grid 0.133 mm (62x192x62), 25139 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (2 of 25139 samples); thinnest 0.13 mm at (151.8, -6.3, 5.5) in 2 region(s); no region is a wall, 2 taper(s) at feature edges (0.01% of surface, budget 2%); 2 more within measurement error of the limit |
| thickness distribution | PASS | median 2.93 mm, p95 7.60 mm, max 24.93 mm |
| hollowable at 1.20 mm wall | WARN | 0.01 of 0.32 cm3 (2%) in 1 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (150.2, 6.3, 5.4) | 1 | 0.0 | 0.0 | 0.18 |
| 2 | taper | 0.13 mm | (151.8, -6.3, 5.5) | 1 | 0.0 | 0.0 | 0.17 |

Measured on the exported STL. The fix belongs in the generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
