# Thickness and hollow

`part_flipper_left_guard.step.py --nozzle 0.4 --report measure/flipper-guard-repair/check_thickness-left.md`

part_flipper_left_guard.step.py: 16.02 cm3 solid, grid 0.251 mm (472x257x92), 200117 surface samples, thickness resolved to 0.126 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.13) | PASS | 0.0% of surface below (17 of 200117 samples); thinnest 0.50 mm at (-61.5, 45.3, 22.0) in 7 region(s); no region is a wall, 7 taper(s) at feature edges (0.01% of surface, budget 2%); 162 more within measurement error of the limit |
| thickness distribution | PASS | median 2.89 mm, p95 24.01 mm, max 115.40 mm |
| hollowable at 1.20 mm wall | WARN | 1.82 of 16.02 cm3 (11%) in 1 pocket(s), 11 too small to shell |
| filament that would save | PASS | 0.27 cm3, 0.3 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.50 mm | (-61.5, 45.3, 22.0) | 5 | 0.3 | 1.5 | 0.21 |
| 2 | taper | 0.50 mm | (-61.5, 40.7, 22.0) | 3 | 0.2 | 1.1 | 0.17 |
| 3 | taper | 0.50 mm | (-59.5, 14.8, 22.0) | 3 | 0.2 | 0.7 | 0.25 |
| 4 | taper | 0.50 mm | (-63.4, 13.4, 22.0) | 2 | 0.1 | 1.5 | 0.08 |
| 5 | taper | 0.63 mm | (43.6, 28.2, 21.4) | 2 | 0.1 | 0.4 | 0.26 |
| 6 | taper | 0.50 mm | (43.2, 23.6, 22.0) | 1 | 0.1 | 0.0 | 0.30 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
