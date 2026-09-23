# Thickness and hollow

`artifacts/make/r0001/product/mintfin/part_body_01_rear.step.py --nozzle 0.4 --min-wall 1.2 --report artifacts/make/r0001/product/mintfin/measure/wish-thickness-body_01_rear.md`

part_body_01_rear.step.py: 5.58 cm3 solid, grid 0.200 mm (292x221x43), 106811 surface samples, thickness resolved to 0.100 mm

| check | status | detail |
|---|---|---|
| wall >= 1.20 mm (+/-0.10) | PASS | 0.1% of surface below (106 of 106811 samples); thinnest 0.40 mm at (0.5, -1.3, 3.3) in 10 region(s); no region is a wall, 10 taper(s) at feature edges (0.10% of surface, budget 2%); 26 more within measurement error of the limit |
| thickness distribution | PASS | median 3.10 mm, p95 18.40 mm, max 57.50 mm |
| hollowable at 1.20 mm wall | WARN | 0.93 of 5.58 cm3 (17%) in 1 pocket(s) |
| filament that would save | PASS | 0.14 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.60 mm | (-3.3, -11.5, 7.7) | 40 | 1.7 | 9.8 | 0.17 |
| 2 | taper | 0.80 mm | (0.8, -3.7, 7.7) | 32 | 1.4 | 8.6 | 0.16 |
| 3 | taper | 0.90 mm | (-0.5, -15.2, 7.5) | 14 | 0.7 | 3.8 | 0.18 |
| 4 | taper | 0.40 mm | (-7.1, -7.7, 3.9) | 7 | 0.4 | 1.4 | 0.25 |
| 5 | taper | 0.40 mm | (7.1, -7.7, 3.6) | 4 | 0.2 | 1.4 | 0.12 |
| 6 | taper | 0.80 mm | (-6.9, -7.8, 5.8) | 2 | 0.1 | 1.0 | 0.10 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
