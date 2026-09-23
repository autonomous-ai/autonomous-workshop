# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_bull_body.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/bull_body/r0004/thickness-bull_body.md`

part_bull_body.step.py: 31.60 cm3 solid, grid 0.251 mm (315x303x121), 244368 surface samples, thickness resolved to 0.126 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.13) | FAIL | 0.1% of surface below (175 of 244368 samples); thinnest 0.25 mm at (1.4, 25.8, 24.9) in 12 region(s); 1 wall(s) (widest band 0.84 mm), 11 taper(s) at feature edges (0.06% of surface, budget 2%); 103 more within measurement error of the limit |
| thickness distribution | PASS | median 4.27 mm, p95 40.06 mm, max 81.33 mm |
| hollowable at 1.20 mm wall | WARN | 13.25 of 31.60 cm3 (42%) in 1 pocket(s), 1 too small to shell |
| filament that would save | PASS | 1.99 cm3, 2.5 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.38 mm | (1.5, 33.2, 26.1) | 29 | 2.2 | 2.6 | 0.84 |
| 2 | taper | 0.38 mm | (-1.6, 25.8, 26.2) | 21 | 1.4 | 2.6 | 0.54 |
| 3 | taper | 0.25 mm | (1.4, 25.8, 24.9) | 17 | 1.2 | 2.6 | 0.46 |
| 4 | taper | 0.25 mm | (25.6, -31.2, 17.9) | 16 | 1.2 | 2.4 | 0.49 |
| 5 | taper | 0.25 mm | (-1.6, 33.2, 25.9) | 17 | 1.1 | 2.7 | 0.39 |
| 6 | taper | 0.25 mm | (28.6, -23.8, 18.9) | 14 | 1.0 | 2.5 | 0.40 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
