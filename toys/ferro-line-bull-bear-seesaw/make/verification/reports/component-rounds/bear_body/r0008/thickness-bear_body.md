# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_bear_body.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/bear_body/r0008/thickness-bear_body.md`

part_bear_body.step.py: 24.55 cm3 solid, grid 0.251 mm (307x311x121), 224140 surface samples, thickness resolved to 0.126 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.13) | FAIL | 0.1% of surface below (255 of 224140 samples); thinnest 0.25 mm at (-1.6, 34.7, 24.6) in 7 region(s); 1 wall(s) (widest band 3.63 mm), 6 taper(s) at feature edges (0.02% of surface, budget 2%); 85 more within measurement error of the limit |
| thickness distribution | PASS | median 4.02 mm, p95 38.59 mm, max 82.47 mm |
| hollowable at 1.20 mm wall | WARN | 8.26 of 24.55 cm3 (34%) in 1 pocket(s) |
| filament that would save | PASS | 1.24 cm3, 1.5 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.25 mm | (-15.3, -31.9, 3.2) | 201 | 15.0 | 4.1 | 3.63 |
| 2 | taper | 0.38 mm | (1.5, 26.3, 24.6) | 12 | 0.9 | 2.0 | 0.44 |
| 3 | taper | 0.50 mm | (-14.4, -20.5, 0.9) | 13 | 0.9 | 1.3 | 0.66 |
| 4 | taper | 0.25 mm | (-1.6, 34.7, 24.6) | 13 | 0.8 | 2.4 | 0.34 |
| 5 | taper | 0.38 mm | (-1.6, 26.3, 26.9) | 8 | 0.5 | 2.4 | 0.21 |
| 6 | taper | 0.63 mm | (-7.4, -20.8, 0.4) | 5 | 0.3 | 1.0 | 0.28 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
