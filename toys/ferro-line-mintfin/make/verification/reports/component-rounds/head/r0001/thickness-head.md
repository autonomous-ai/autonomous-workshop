# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_head.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/head/r0001/thickness-head.md`

part_head.step.py: 19.68 cm3 solid, grid 0.170 mm (229x322x152), 202242 surface samples, thickness resolved to 0.085 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.09) | FAIL | 0.8% of surface below (1245 of 202242 samples); thinnest 0.17 mm at (0.9, -15.0, 19.8) in 8 region(s); 3 wall(s) (widest band 1.36 mm), 5 taper(s) at feature edges (0.07% of surface, budget 2%); 115 more within measurement error of the limit |
| thickness distribution | PASS | median 17.53 mm, p95 44.33 mm, max 55.39 mm |
| hollowable at 1.20 mm wall | WARN | 13.26 of 19.68 cm3 (67%) in 2 pocket(s) |
| filament that would save | PASS | 1.99 cm3, 2.5 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.17 mm | (25.3, 14.7, 19.8) | 544 | 22.6 | 16.6 | 1.36 |
| 2 | wall | 0.17 mm | (25.2, -14.8, 20.0) | 491 | 20.7 | 16.5 | 1.25 |
| 3 | wall | 0.17 mm | (0.9, -15.0, 19.8) | 82 | 3.0 | 2.9 | 1.04 |
| 4 | taper | 0.26 mm | (0.8, 15.0, 19.4) | 56 | 2.1 | 2.7 | 0.77 |
| 5 | taper | 0.17 mm | (21.7, -12.7, 18.6) | 35 | 1.2 | 1.9 | 0.59 |
| 6 | taper | 0.17 mm | (21.7, 12.8, 18.8) | 32 | 1.1 | 2.0 | 0.55 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
