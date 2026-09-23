# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/part_axle.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/measure/component-rounds/axle/r0003/thickness-axle.md`

part_axle.step.py: 4.37 cm3 solid, grid 0.140 mm (169x169x394), 275959 surface samples, thickness resolved to 0.070 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 1.2% of surface below (2912 of 275959 samples); thinnest 0.14 mm at (2.1, -8.0, 0.1) in 11 region(s); 4 wall(s) (widest band 1.03 mm), 7 taper(s) at feature edges (0.15% of surface, budget 2%); 854 more within measurement error of the limit |
| thickness distribution | PASS | median 1.75 mm, p95 3.50 mm, max 54.46 mm |
| hollowable at 1.20 mm wall | WARN | 0.01 of 4.37 cm3 (0%) in 1 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.35 mm | (-9.5, -6.2, 36.8) | 1521 | 33.2 | 32.3 | 1.03 |
| 2 | wall | 0.14 mm | (-0.1, 8.2, 54.5) | 462 | 11.7 | 12.6 | 0.93 |
| 3 | wall | 0.14 mm | (-7.9, -3.7, 26.8) | 359 | 10.5 | 11.4 | 0.92 |
| 4 | taper | 0.14 mm | (4.4, -7.2, 47.3) | 236 | 8.2 | 12.8 | 0.65 |
| 5 | wall | 0.14 mm | (2.1, -8.0, 0.1) | 304 | 8.2 | 9.2 | 0.89 |
| 6 | taper | 0.14 mm | (2.3, -8.0, 47.3) | 6 | 0.3 | 1.3 | 0.24 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
