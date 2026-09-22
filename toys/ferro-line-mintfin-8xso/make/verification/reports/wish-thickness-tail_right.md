# Thickness and hollow

`artifacts/make/r0001/product/mintfin/part_tail_right.step.py --nozzle .4 --min-wall 1.2 --report artifacts/make/r0001/product/mintfin/measure/wish-thickness-tail_right.md`

part_tail_right.step.py: 3.53 cm3 solid, grid 0.200 mm (200x248x27), 62497 surface samples, thickness resolved to 0.100 mm

| check | status | detail |
|---|---|---|
| wall >= 1.20 mm (+/-0.10) | PASS | 0.2% of surface below (108 of 62497 samples); thinnest 0.20 mm at (131.3, 45.8, 0.0) in 5 region(s); no region is a wall, 5 taper(s) at feature edges (0.17% of surface, budget 2%); 6 more within measurement error of the limit |
| thickness distribution | PASS | median 4.00 mm, p95 23.90 mm, max 45.00 mm |
| hollowable at 1.20 mm wall | WARN | 0.95 of 3.53 cm3 (27%) in 2 pocket(s), 3 too small to shell |
| filament that would save | PASS | 0.14 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.20 mm | (128.5, 53.2, 0.0) | 83 | 3.1 | 13.1 | 0.24 |
| 2 | taper | 0.20 mm | (123.9, 67.3, 0.5) | 8 | 0.7 | 1.5 | 0.48 |
| 3 | taper | 0.20 mm | (131.3, 45.8, 0.0) | 13 | 0.5 | 3.7 | 0.14 |
| 4 | taper | 0.50 mm | (124.0, 67.4, 3.7) | 2 | 0.2 | 0.1 | 0.79 |
| 5 | taper | 0.40 mm | (134.2, 50.8, -0.0) | 2 | 0.1 | 0.3 | 0.27 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
