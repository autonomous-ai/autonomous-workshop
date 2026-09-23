# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_bear_body.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/bear_body/r0007/thickness-bear_body.md`

part_bear_body.step.py: 27.67 cm3 solid, grid 0.251 mm (307x311x121), 238406 surface samples, thickness resolved to 0.126 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.13) | FAIL | 0.7% of surface below (1634 of 238406 samples); thinnest 0.25 mm at (31.3, -25.6, 13.4) in 18 region(s); 3 wall(s) (widest band 5.42 mm), 15 taper(s) at feature edges (0.07% of surface, budget 2%); 294 more within measurement error of the limit |
| thickness distribution | PASS | median 4.02 mm, p95 39.85 mm, max 82.47 mm |
| hollowable at 1.20 mm wall | WARN | 10.42 of 27.67 cm3 (38%) in 1 pocket(s) |
| filament that would save | PASS | 1.56 cm3, 1.9 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.25 mm | (-15.0, -32.0, 9.7) | 1025 | 69.7 | 12.9 | 5.42 |
| 2 | wall | 0.25 mm | (31.3, -25.6, 13.4) | 241 | 18.0 | 9.7 | 1.85 |
| 3 | wall | 0.25 mm | (-31.1, -25.7, 6.9) | 214 | 16.8 | 9.4 | 1.78 |
| 4 | taper | 0.25 mm | (-23.4, -27.8, 18.4) | 21 | 1.4 | 2.5 | 0.54 |
| 5 | taper | 0.25 mm | (26.6, -27.8, 19.0) | 16 | 1.1 | 2.0 | 0.56 |
| 6 | taper | 0.38 mm | (-26.5, -35.2, 19.5) | 14 | 1.0 | 2.3 | 0.44 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
