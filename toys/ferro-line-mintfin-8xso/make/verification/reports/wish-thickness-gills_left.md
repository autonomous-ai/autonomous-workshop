# Thickness and hollow

`artifacts/make/r0001/product/mintfin/part_gills_left.step.py --nozzle .4 --min-wall 1.2 --report artifacts/make/r0001/product/mintfin/measure/wish-thickness-gills_left.md`

part_gills_left.step.py: 1.73 cm3 solid, grid 0.200 mm (192x263x23), 42221 surface samples, thickness resolved to 0.100 mm

| check | status | detail |
|---|---|---|
| wall >= 1.20 mm (+/-0.10) | PASS | 0.3% of surface below (148 of 42221 samples); thinnest 0.40 mm at (-4.7, 4.0, 2.7) in 8 region(s); no region is a wall, 8 taper(s) at feature edges (0.30% of surface, budget 2%); 265 more within measurement error of the limit |
| thickness distribution | PASS | median 2.40 mm, p95 11.20 mm, max 37.80 mm |
| hollowable at 1.20 mm wall | WARN | 0.02 of 1.73 cm3 (1%) in 3 pocket(s), 1 too small to shell |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.90 mm | (-32.8, 10.2, 3.3) | 50 | 2.1 | 6.6 | 0.31 |
| 2 | taper | 0.70 mm | (-19.5, 30.6, 3.5) | 48 | 2.0 | 4.7 | 0.42 |
| 3 | taper | 0.90 mm | (-27.2, -14.8, 3.5) | 39 | 1.6 | 5.1 | 0.31 |
| 4 | taper | 1.00 mm | (-22.4, 34.4, 0.8) | 5 | 0.3 | 1.0 | 0.29 |
| 5 | taper | 1.00 mm | (-16.4, 27.9, 3.2) | 3 | 0.1 | 0.5 | 0.26 |
| 6 | taper | 1.00 mm | (-23.4, -12.3, 3.3) | 1 | 0.0 | 0.0 | 0.21 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
