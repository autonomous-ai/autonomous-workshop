# Thickness and hollow

`part_lane_05_yellow.step.py --nozzle 0.4 --report measure/thickness-lane_05_yellow.md`

part_lane_05_yellow.step.py: 1.35 cm3 solid, grid 0.133 mm (411x200x27), 87116 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (12 of 87116 samples); thinnest 0.13 mm at (75.1, 26.0, 1.0) in 6 region(s); no region is a wall, 6 taper(s) at feature edges (0.01% of surface, budget 2%); 29 more within measurement error of the limit |
| thickness distribution | PASS | median 2.13 mm, p95 9.47 mm, max 53.20 mm |
| hollowable at 1.20 mm wall | PASS | 0.00 of 1.35 cm3 (0%) in 0 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (75.1, 26.0, 1.0) | 2 | 0.0 | 0.2 | 0.20 |
| 2 | taper | 0.20 mm | (72.8, 23.1, 2.2) | 2 | 0.0 | 0.3 | 0.11 |
| 3 | taper | 0.60 mm | (75.4, 25.1, 0.9) | 1 | 0.0 | 0.0 | 0.14 |
| 4 | taper | 0.73 mm | (77.8, 16.3, 0.1) | 1 | 0.0 | 0.0 | 0.12 |
| 5 | taper | 0.13 mm | (24.7, 9.7, 0.1) | 5 | 0.0 | 0.1 | 0.01 |
| 6 | taper | 0.73 mm | (26.3, 4.1, 0.0) | 1 | 0.0 | 0.0 | 0.01 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
