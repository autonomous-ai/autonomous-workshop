# Thickness and hollow

`part_foot_front_right.step.py --nozzle 0.4 --report measure/thickness-foot_front_right.md`

part_foot_front_right.step.py: 21.07 cm3 solid, grid 0.188 mm (292x175x210), 287225 surface samples, thickness resolved to 0.094 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.09) | PASS | 0.0% of surface below (30 of 287225 samples); thinnest 0.19 mm at (10.5, 6.1, 5.9) in 3 region(s); no region is a wall, 2 taper(s) at feature edges and 1 spot(s) too small to be a wall (0.04% of surface, budget 2%); 118 more within measurement error of the limit |
| thickness distribution | PASS | median 6.00 mm, p95 35.93 mm, max 53.85 mm |
| hollowable at 1.20 mm wall | WARN | 9.81 of 21.07 cm3 (47%) in 1 pocket(s) |
| filament that would save | PASS | 1.47 cm3, 1.8 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.19 mm | (10.5, 6.1, 5.9) | 20 | 2.2 | 3.1 | 0.70 |
| 2 | taper | 0.19 mm | (4.0, 6.2, 5.9) | 9 | 1.5 | 2.3 | 0.64 |
| 3 | spot | 0.28 mm | (6.7, 6.1, 5.8) | 1 | 0.2 | 0.0 | 0.88 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
