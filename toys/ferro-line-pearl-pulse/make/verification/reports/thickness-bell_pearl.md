# Thickness and hollow

`artifacts/make/r0001/product/cad/part_bell_pearl.step.py --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-bell_pearl.md`

part_bell_pearl.step.py: 8.81 cm3 solid, grid 0.228 mm (362x362x84), 258824 surface samples, thickness resolved to 0.114 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.11) | PASS | 0.5% of surface below (1360 of 258824 samples); thinnest 0.23 mm at (26.5, 17.8, 8.9) in 21 region(s); no region is a wall, 20 taper(s) at feature edges and 1 spot(s) too small to be a wall (0.46% of surface, budget 2%); 1595 more within measurement error of the limit |
| thickness distribution | PASS | median 1.14 mm, p95 3.08 mm, max 42.64 mm |
| hollowable at 1.20 mm wall | WARN | 0.00 of 8.81 cm3 (0%) in 2 pocket(s), 37 too small to shell |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.34 mm | (-18.7, -35.4, 17.8) | 488 | 22.4 | 65.8 | 0.34 |
| 2 | taper | 0.23 mm | (27.9, -29.6, 18.0) | 429 | 19.6 | 66.5 | 0.29 |
| 3 | taper | 0.34 mm | (3.2, 39.9, 18.0) | 369 | 16.6 | 56.9 | 0.29 |
| 4 | taper | 0.34 mm | (4.4, -39.5, 18.0) | 26 | 1.3 | 6.5 | 0.20 |
| 5 | taper | 0.34 mm | (26.8, 30.1, 17.5) | 18 | 1.0 | 3.4 | 0.28 |
| 6 | taper | 0.46 mm | (12.1, 37.3, 16.9) | 5 | 0.3 | 1.5 | 0.21 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
