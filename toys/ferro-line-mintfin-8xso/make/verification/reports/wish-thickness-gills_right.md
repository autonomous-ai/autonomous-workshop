# Thickness and hollow

`artifacts/make/r0001/product/mintfin/part_gills_right.step.py --nozzle .4 --min-wall 1.2 --report artifacts/make/r0001/product/mintfin/measure/wish-thickness-gills_right.md`

part_gills_right.step.py: 1.73 cm3 solid, grid 0.200 mm (192x263x23), 42474 surface samples, thickness resolved to 0.100 mm

| check | status | detail |
|---|---|---|
| wall >= 1.20 mm (+/-0.10) | PASS | 0.3% of surface below (156 of 42474 samples); thinnest 0.20 mm at (22.4, 34.7, 0.3) in 5 region(s); no region is a wall, 5 taper(s) at feature edges (0.32% of surface, budget 2%); 215 more within measurement error of the limit |
| thickness distribution | PASS | median 2.40 mm, p95 11.30 mm, max 37.70 mm |
| hollowable at 1.20 mm wall | WARN | 0.02 of 1.73 cm3 (1%) in 3 pocket(s), 1 too small to shell |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.80 mm | (31.3, 9.8, 3.5) | 51 | 2.1 | 6.5 | 0.32 |
| 2 | taper | 0.90 mm | (19.1, 29.9, 3.4) | 48 | 2.0 | 4.4 | 0.45 |
| 3 | taper | 0.80 mm | (26.6, -14.6, 3.5) | 48 | 2.0 | 5.3 | 0.37 |
| 4 | taper | 0.20 mm | (22.4, 34.7, 0.3) | 8 | 0.4 | 1.3 | 0.35 |
| 5 | taper | 1.00 mm | (26.7, 8.4, 3.1) | 1 | 0.0 | 0.0 | 0.20 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
