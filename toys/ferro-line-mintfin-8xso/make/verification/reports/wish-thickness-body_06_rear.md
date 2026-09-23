# Thickness and hollow

`artifacts/make/r0001/product/mintfin/part_body_06_rear.step.py --nozzle .4 --min-wall 1.2 --report artifacts/make/r0001/product/mintfin/measure/wish-thickness-body_06_rear.md`

part_body_06_rear.step.py: 1.62 cm3 solid, grid 0.200 mm (140x120x39), 35384 surface samples, thickness resolved to 0.100 mm

| check | status | detail |
|---|---|---|
| wall >= 1.20 mm (+/-0.10) | PASS | 1.2% of surface below (438 of 35384 samples); thinnest 0.20 mm at (-0.8, -0.4, 6.7) in 9 region(s); no region is a wall, 9 taper(s) at feature edges (1.20% of surface, budget 2%); 68 more within measurement error of the limit |
| thickness distribution | PASS | median 3.40 mm, p95 12.80 mm, max 27.10 mm |
| hollowable at 1.20 mm wall | WARN | 0.23 of 1.62 cm3 (14%) in 1 pocket(s) |
| filament that would save | PASS | 0.03 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.20 mm | (0.9, -0.4, 6.7) | 199 | 8.0 | 9.3 | 0.86 |
| 2 | taper | 0.20 mm | (-0.8, -0.4, 6.7) | 106 | 4.2 | 5.1 | 0.84 |
| 3 | taper | 0.20 mm | (-3.9, -5.1, 6.7) | 97 | 4.0 | 5.2 | 0.77 |
| 4 | taper | 0.80 mm | (6.6, -3.6, 4.3) | 13 | 0.6 | 3.2 | 0.19 |
| 5 | taper | 0.90 mm | (-0.5, 2.1, 5.0) | 9 | 0.4 | 1.8 | 0.25 |
| 6 | taper | 0.60 mm | (0.6, -10.8, 6.4) | 5 | 0.2 | 1.6 | 0.14 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
