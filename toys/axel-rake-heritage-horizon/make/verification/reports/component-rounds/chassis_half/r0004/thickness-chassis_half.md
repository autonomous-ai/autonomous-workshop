# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/heritage/part_chassis_half.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/heritage/measure/component-rounds/chassis_half/r0004/thickness-chassis_half.md`

part_chassis_half.step.py: 30.58 cm3 solid, grid 0.239 mm (603x250x74), 174663 surface samples, thickness resolved to 0.120 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.12) | FAIL | 0.9% of surface below (1490 of 174663 samples); thinnest 0.24 mm at (20.8, -45.8, 13.1) in 7 region(s); 1 wall(s) (widest band 7.40 mm), 6 taper(s) at feature edges (0.01% of surface, budget 2%); 29 more within measurement error of the limit |
| thickness distribution | PASS | median 12.93 mm, p95 47.05 mm, max 67.64 mm |
| hollowable at 1.20 mm wall | WARN | 19.27 of 30.58 cm3 (63%) in 2 pocket(s), 1 too small to shell |
| filament that would save | PASS | 2.89 cm3, 3.6 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.36 mm | (-32.8, -32.7, 12.0) | 1469 | 93.8 | 12.7 | 7.40 |
| 2 | taper | 0.24 mm | (20.8, -45.8, 13.1) | 13 | 1.0 | 2.0 | 0.52 |
| 3 | taper | 0.48 mm | (-19.8, -46.1, 14.9) | 3 | 0.2 | 0.5 | 0.45 |
| 4 | taper | 0.48 mm | (19.3, -51.4, 0.0) | 2 | 0.1 | 1.1 | 0.12 |
| 5 | taper | 0.24 mm | (22.9, -37.0, 0.3) | 1 | 0.1 | 0.0 | 0.41 |
| 6 | taper | 0.60 mm | (16.5, -51.7, 0.2) | 1 | 0.1 | 0.0 | 0.23 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
