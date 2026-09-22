# Thickness and hollow

`artifacts/make/r0001/product/mintfin/part_body_05_rear.step.py --nozzle .4 --min-wall 1.2 --report artifacts/make/r0001/product/mintfin/measure/wish-thickness-body_05_rear.md`

part_body_05_rear.step.py: 2.82 cm3 solid, grid 0.200 mm (186x156x41), 55848 surface samples, thickness resolved to 0.100 mm

| check | status | detail |
|---|---|---|
| wall >= 1.20 mm (+/-0.10) | PASS | 0.9% of surface below (487 of 55848 samples); thinnest 0.20 mm at (3.5, -8.0, 7.1) in 13 region(s); no region is a wall, 12 taper(s) at feature edges and 1 spot(s) too small to be a wall (0.89% of surface, budget 2%); 71 more within measurement error of the limit |
| thickness distribution | PASS | median 3.40 mm, p95 18.70 mm, max 36.20 mm |
| hollowable at 1.20 mm wall | WARN | 0.50 of 2.82 cm3 (18%) in 1 pocket(s) |
| filament that would save | PASS | 0.08 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.20 mm | (-1.4, -2.4, 7.1) | 203 | 7.9 | 9.4 | 0.84 |
| 2 | taper | 0.20 mm | (3.5, -8.0, 7.1) | 110 | 4.4 | 5.2 | 0.86 |
| 3 | taper | 0.20 mm | (-3.8, -7.0, 7.1) | 103 | 4.4 | 5.1 | 0.86 |
| 4 | spot | 0.20 mm | (0.5, -13.8, 2.9) | 39 | 2.5 | 1.7 | 1.47 |
| 5 | taper | 0.20 mm | (0.6, -12.7, 6.5) | 20 | 0.9 | 4.1 | 0.23 |
| 6 | taper | 0.80 mm | (6.4, -6.6, 3.5) | 3 | 0.1 | 1.5 | 0.10 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
