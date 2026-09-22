# Thickness and hollow

`artifacts/make/r0001/product/mintfin/part_head_rear.step.py --nozzle .4 --min-wall 1.2 --report artifacts/make/r0001/product/mintfin/measure/wish-thickness-head_rear.md`

part_head_rear.step.py: 49.29 cm3 solid, grid 0.210 mm (321x224x152), 192626 surface samples, thickness resolved to 0.105 mm

| check | status | detail |
|---|---|---|
| wall >= 1.20 mm (+/-0.10) | PASS | 0.3% of surface below (509 of 192626 samples); thinnest 0.21 mm at (-1.4, -22.6, 5.5) in 34 region(s); no region is a wall, 33 taper(s) at feature edges and 1 spot(s) too small to be a wall (0.28% of surface, budget 2%); 95 more within measurement error of the limit |
| thickness distribution | PASS | median 25.41 mm, p95 46.72 mm, max 65.10 mm |
| hollowable at 1.20 mm wall | WARN | 39.06 of 49.29 cm3 (79%) in 1 pocket(s) |
| filament that would save | PASS | 5.86 cm3, 7.3 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.21 mm | (-1.4, -22.6, 5.5) | 93 | 5.5 | 8.6 | 0.64 |
| 2 | taper | 0.32 mm | (-4.0, 8.4, 30.8) | 88 | 3.7 | 5.7 | 0.65 |
| 3 | taper | 0.32 mm | (2.9, 2.5, 30.8) | 86 | 3.6 | 5.8 | 0.62 |
| 4 | taper | 0.32 mm | (-3.9, 3.9, 30.8) | 77 | 3.4 | 5.5 | 0.62 |
| 5 | taper | 0.53 mm | (1.0, 10.3, 30.6) | 74 | 3.2 | 5.6 | 0.57 |
| 6 | taper | 0.95 mm | (-0.5, -0.9, 30.8) | 20 | 1.1 | 7.2 | 0.15 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
