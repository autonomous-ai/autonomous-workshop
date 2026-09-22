# Thickness and hollow

`artifacts/make/r0001/product/mintfin/part_body_02_rear.step.py --nozzle .4 --min-wall 1.2 --report artifacts/make/r0001/product/mintfin/measure/wish-thickness-body_02_rear.md`

part_body_02_rear.step.py: 5.90 cm3 solid, grid 0.200 mm (303x224x46), 112832 surface samples, thickness resolved to 0.100 mm

| check | status | detail |
|---|---|---|
| wall >= 1.20 mm (+/-0.10) | PASS | 0.4% of surface below (475 of 112832 samples); thinnest 0.20 mm at (-2.0, -5.1, 8.1) in 13 region(s); no region is a wall, 13 taper(s) at feature edges (0.42% of surface, budget 2%); 93 more within measurement error of the limit |
| thickness distribution | PASS | median 3.10 mm, p95 17.70 mm, max 59.60 mm |
| hollowable at 1.20 mm wall | WARN | 0.97 of 5.90 cm3 (16%) in 1 pocket(s) |
| filament that would save | PASS | 0.15 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.20 mm | (1.5, -4.9, 8.1) | 215 | 8.9 | 9.8 | 0.91 |
| 2 | taper | 0.20 mm | (-2.0, -5.1, 8.1) | 212 | 8.8 | 9.8 | 0.89 |
| 3 | taper | 0.20 mm | (0.1, -14.3, 1.5) | 32 | 1.4 | 1.3 | 1.06 |
| 4 | taper | 0.20 mm | (-6.8, -8.3, 3.2) | 3 | 0.1 | 1.2 | 0.12 |
| 5 | taper | 0.40 mm | (-0.5, -15.6, 8.1) | 2 | 0.1 | 0.3 | 0.36 |
| 6 | taper | 0.80 mm | (6.8, -8.2, 4.0) | 2 | 0.1 | 0.1 | 0.46 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
