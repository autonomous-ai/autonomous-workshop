# Thickness and hollow

`artifacts/make/r0001/product/mintfin/part_body_04_rear.step.py --nozzle .4 --min-wall 1.2 --report artifacts/make/r0001/product/mintfin/measure/wish-thickness-body_04_rear.md`

part_body_04_rear.step.py: 4.34 cm3 solid, grid 0.200 mm (239x197x46), 84358 surface samples, thickness resolved to 0.100 mm

| check | status | detail |
|---|---|---|
| wall >= 1.20 mm (+/-0.10) | PASS | 0.1% of surface below (59 of 84358 samples); thinnest 0.30 mm at (-6.6, -7.5, 3.3) in 12 region(s); no region is a wall, 12 taper(s) at feature edges (0.08% of surface, budget 2%); 78 more within measurement error of the limit |
| thickness distribution | PASS | median 3.10 mm, p95 13.80 mm, max 46.90 mm |
| hollowable at 1.20 mm wall | WARN | 0.68 of 4.34 cm3 (16%) in 1 pocket(s) |
| filament that would save | PASS | 0.10 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.70 mm | (-3.2, -5.2, 8.2) | 13 | 0.7 | 4.7 | 0.14 |
| 2 | taper | 0.80 mm | (-0.7, -1.3, 3.8) | 12 | 0.6 | 3.4 | 0.17 |
| 3 | taper | 0.70 mm | (2.4, -11.5, 8.2) | 12 | 0.6 | 4.0 | 0.15 |
| 4 | taper | 0.50 mm | (-0.6, -14.7, 3.4) | 5 | 0.2 | 1.8 | 0.14 |
| 5 | taper | 0.70 mm | (-3.5, -10.3, 8.2) | 5 | 0.2 | 0.8 | 0.28 |
| 6 | taper | 0.30 mm | (-6.6, -7.5, 3.3) | 4 | 0.2 | 1.5 | 0.12 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
