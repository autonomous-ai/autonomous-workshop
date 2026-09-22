# Thickness and hollow

`artifacts/make/r0001/product/mintfin/part_body_03_rear.step.py --nozzle .4 --min-wall 1.2 --report artifacts/make/r0001/product/mintfin/measure/wish-thickness-body_03_rear.md`

part_body_03_rear.step.py: 5.07 cm3 solid, grid 0.200 mm (270x208x46), 97747 surface samples, thickness resolved to 0.100 mm

| check | status | detail |
|---|---|---|
| wall >= 1.20 mm (+/-0.10) | PASS | 0.5% of surface below (465 of 97747 samples); thinnest 0.20 mm at (-1.4, -4.3, 8.1) in 12 region(s); no region is a wall, 12 taper(s) at feature edges (0.49% of surface, budget 2%); 65 more within measurement error of the limit |
| thickness distribution | PASS | median 3.10 mm, p95 17.30 mm, max 53.00 mm |
| hollowable at 1.20 mm wall | WARN | 0.83 of 5.07 cm3 (16%) in 1 pocket(s) |
| filament that would save | PASS | 0.12 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.20 mm | (-1.4, -4.3, 8.1) | 213 | 8.7 | 9.8 | 0.89 |
| 2 | taper | 0.20 mm | (0.9, -4.2, 8.1) | 181 | 7.7 | 9.9 | 0.78 |
| 3 | taper | 0.20 mm | (0.6, -15.2, 3.5) | 14 | 0.7 | 2.7 | 0.26 |
| 4 | taper | 0.60 mm | (-6.7, -8.8, 3.2) | 10 | 0.6 | 3.5 | 0.16 |
| 5 | taper | 0.40 mm | (0.6, -1.5, 7.7) | 11 | 0.5 | 4.4 | 0.12 |
| 6 | taper | 0.20 mm | (6.7, -8.8, 8.2) | 7 | 0.5 | 2.6 | 0.20 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
