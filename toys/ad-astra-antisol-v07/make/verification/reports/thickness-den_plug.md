# Thickness and hollow

`part_den_plug.step.py --nozzle 0.4 --report measure/thickness-den_plug.md`

part_den_plug.step.py: 9.90 cm3 solid, grid 0.147 mm (250x250x168), 175412 surface samples, thickness resolved to 0.074 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (11 of 175412 samples); thinnest 0.15 mm at (17.4, -17.7, 24.0) in 3 region(s); no region is a wall, 3 taper(s) at feature edges (0.01% of surface, budget 2%); 26 more within measurement error of the limit |
| thickness distribution | PASS | median 8.23 mm, p95 33.52 mm, max 43.66 mm |
| hollowable at 1.20 mm wall | WARN | 5.75 of 9.90 cm3 (58%) in 3 pocket(s), 1 too small to shell |
| filament that would save | PASS | 0.86 cm3, 1.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.29 mm | (-17.3, -17.7, 24.0) | 4 | 0.1 | 0.7 | 0.12 |
| 2 | taper | 0.15 mm | (17.4, -17.7, 24.0) | 4 | 0.1 | 0.6 | 0.14 |
| 3 | taper | 0.29 mm | (17.1, -12.9, 8.3) | 3 | 0.1 | 0.8 | 0.07 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
