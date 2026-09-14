# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/heritage/part_chassis_half_right.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/heritage/measure/component-rounds/chassis_half_right/r0005/thickness-chassis_half_right.md`

part_chassis_half_right.step.py: 30.36 cm3 solid, grid 0.239 mm (603x250x74), 171969 surface samples, thickness resolved to 0.120 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.12) | PASS | 0.0% of surface below (33 of 171969 samples); thinnest 0.36 mm at (20.8, 45.8, 13.3) in 5 region(s); no region is a wall, 5 taper(s) at feature edges (0.02% of surface, budget 2%); 23 more within measurement error of the limit |
| thickness distribution | PASS | median 12.93 mm, p95 47.05 mm, max 67.88 mm |
| hollowable at 1.20 mm wall | WARN | 19.20 of 30.36 cm3 (63%) in 2 pocket(s), 1 too small to shell |
| filament that would save | PASS | 2.88 cm3, 3.6 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.36 mm | (20.8, 45.8, 13.3) | 15 | 1.1 | 2.0 | 0.57 |
| 2 | taper | 0.36 mm | (-19.9, 45.8, 13.1) | 15 | 1.0 | 2.2 | 0.48 |
| 3 | taper | 0.48 mm | (19.2, 51.5, 0.0) | 1 | 0.1 | 0.0 | 0.31 |
| 4 | taper | 0.48 mm | (1.4, 49.0, 0.0) | 1 | 0.1 | 0.0 | 0.23 |
| 5 | taper | 0.60 mm | (16.5, 51.6, 0.1) | 1 | 0.1 | 0.0 | 0.23 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
