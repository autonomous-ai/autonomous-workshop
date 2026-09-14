# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/heritage/part_chassis_half_right.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/heritage/measure/component-rounds/chassis_half_right/r0004/thickness-chassis_half_right.md`

part_chassis_half_right.step.py: 30.49 cm3 solid, grid 0.239 mm (603x250x74), 172729 surface samples, thickness resolved to 0.120 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.12) | PASS | 0.0% of surface below (33 of 172729 samples); thinnest 0.24 mm at (-1.5, 49.0, 0.0) in 5 region(s); no region is a wall, 5 taper(s) at feature edges (0.02% of surface, budget 2%); 21 more within measurement error of the limit |
| thickness distribution | PASS | median 12.93 mm, p95 47.05 mm, max 66.69 mm |
| hollowable at 1.20 mm wall | WARN | 19.23 of 30.49 cm3 (63%) in 2 pocket(s), 1 too small to shell |
| filament that would save | PASS | 2.88 cm3, 3.6 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.24 mm | (20.8, 45.8, 14.9) | 14 | 1.1 | 2.0 | 0.54 |
| 2 | taper | 0.36 mm | (-19.7, 46.1, 13.6) | 13 | 1.0 | 1.9 | 0.52 |
| 3 | taper | 0.48 mm | (1.4, 49.0, 0.0) | 3 | 0.2 | 1.3 | 0.14 |
| 4 | taper | 0.24 mm | (-1.5, 49.0, 0.0) | 2 | 0.1 | 0.0 | 0.46 |
| 5 | taper | 0.36 mm | (16.5, 50.7, 0.1) | 1 | 0.1 | 0.0 | 0.31 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
