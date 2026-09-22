# Thickness and hollow

`artifacts/make/r0001/product/mintfin/part_body_07_rear.step.py --nozzle .4 --min-wall 1.2 --report artifacts/make/r0001/product/mintfin/measure/wish-thickness-body_07_rear.md`

part_body_07_rear.step.py: 0.90 cm3 solid, grid 0.200 mm (102x90x39), 23004 surface samples, thickness resolved to 0.100 mm

| check | status | detail |
|---|---|---|
| wall >= 1.20 mm (+/-0.10) | PASS | 0.8% of surface below (155 of 23004 samples); thinnest 0.20 mm at (3.9, -1.2, 1.5) in 12 region(s); no region is a wall, 12 taper(s) at feature edges (0.76% of surface, budget 2%); 26 more within measurement error of the limit |
| thickness distribution | PASS | median 3.40 mm, p95 6.80 mm, max 9.70 mm |
| hollowable at 1.20 mm wall | WARN | 0.07 of 0.90 cm3 (8%) in 3 pocket(s) |
| filament that would save | PASS | 0.01 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.60 mm | (-3.6, -0.2, 6.9) | 43 | 1.9 | 8.7 | 0.22 |
| 2 | taper | 0.40 mm | (-7.8, -2.3, 3.1) | 21 | 1.4 | 2.1 | 0.66 |
| 3 | taper | 0.30 mm | (7.7, -1.3, 3.2) | 17 | 1.0 | 2.1 | 0.49 |
| 4 | taper | 0.80 mm | (4.0, -0.5, 6.9) | 23 | 1.0 | 4.8 | 0.20 |
| 5 | taper | 0.60 mm | (4.0, -2.8, 6.9) | 17 | 0.8 | 4.3 | 0.18 |
| 6 | taper | 0.60 mm | (0.6, 4.8, 4.1) | 12 | 0.6 | 3.5 | 0.16 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
