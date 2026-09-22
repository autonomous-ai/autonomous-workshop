# Thickness and hollow

`artifacts/make/r0001/product/mintfin/part_body_08_rear.step.py --nozzle .4 --min-wall 1.2 --report artifacts/make/r0001/product/mintfin/measure/wish-thickness-body_08_rear.md`

part_body_08_rear.step.py: 0.43 cm3 solid, grid 0.200 mm (73x74x33), 13883 surface samples, thickness resolved to 0.100 mm

| check | status | detail |
|---|---|---|
| wall >= 1.20 mm (+/-0.10) | PASS | 0.6% of surface below (80 of 13883 samples); thinnest 0.20 mm at (6.6, 0.4, 2.1) in 12 region(s); no region is a wall, 12 taper(s) at feature edges (0.57% of surface, budget 2%); 316 more within measurement error of the limit |
| thickness distribution | PASS | median 2.40 mm, p95 5.60 mm, max 5.60 mm |
| hollowable at 1.20 mm wall | PASS | 0.00 of 0.43 cm3 (0%) in 0 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.60 mm | (2.5, -3.2, 5.7) | 14 | 0.6 | 5.5 | 0.11 |
| 2 | taper | 0.50 mm | (-6.6, 0.4, 2.0) | 13 | 0.6 | 4.1 | 0.14 |
| 3 | taper | 0.90 mm | (0.5, 6.2, 3.3) | 11 | 0.5 | 2.5 | 0.21 |
| 4 | taper | 0.80 mm | (-2.0, -3.8, 5.7) | 10 | 0.5 | 3.6 | 0.13 |
| 5 | taper | 0.80 mm | (3.4, 2.1, 5.7) | 8 | 0.4 | 1.1 | 0.39 |
| 6 | taper | 0.80 mm | (-4.0, 0.5, 5.7) | 8 | 0.3 | 3.0 | 0.11 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
