# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_bear_body.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/bear_body/r0003/thickness-bear_body.md`

part_bear_body.step.py: 30.31 cm3 solid, grid 0.251 mm (307x311x121), 241785 surface samples, thickness resolved to 0.126 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.13) | FAIL | 0.5% of surface below (1022 of 241785 samples); thinnest 0.25 mm at (32.3, -24.7, 4.7) in 13 region(s); 2 wall(s) (widest band 3.48 mm), 11 taper(s) at feature edges (0.05% of surface, budget 2%); 266 more within measurement error of the limit |
| thickness distribution | PASS | median 4.27 mm, p95 42.11 mm, max 83.35 mm |
| hollowable at 1.20 mm wall | WARN | 12.35 of 30.31 cm3 (41%) in 1 pocket(s) |
| filament that would save | PASS | 1.85 cm3, 2.3 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.25 mm | (32.3, -24.7, 4.7) | 490 | 35.0 | 10.1 | 3.48 |
| 2 | wall | 0.25 mm | (-32.8, -24.3, 13.5) | 409 | 30.0 | 10.0 | 2.99 |
| 3 | taper | 0.25 mm | (-25.5, -28.2, 18.3) | 24 | 1.7 | 5.2 | 0.33 |
| 4 | taper | 0.50 mm | (1.5, 26.3, 25.8) | 17 | 1.2 | 2.2 | 0.57 |
| 5 | taper | 0.38 mm | (28.6, -20.9, 18.2) | 13 | 0.9 | 2.3 | 0.38 |
| 6 | taper | 0.25 mm | (-25.5, -20.8, 18.6) | 13 | 0.8 | 2.6 | 0.32 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
