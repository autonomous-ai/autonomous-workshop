# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_bear_body.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/bear_body/r0001/thickness-bear_body.md`

part_bear_body.step.py: 38.94 cm3 solid, grid 0.239 mm (322x316x105), 308423 surface samples, thickness resolved to 0.120 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.12) | FAIL | 0.1% of surface below (226 of 308423 samples); thinnest 0.24 mm at (-32.4, 7.4, 4.2) in 5 region(s); 2 wall(s) (widest band 1.54 mm), 3 taper(s) at feature edges (0.02% of surface, budget 2%); 121 more within measurement error of the limit |
| thickness distribution | PASS | median 7.30 mm, p95 42.86 mm, max 82.61 mm |
| hollowable at 1.20 mm wall | WARN | 18.67 of 38.94 cm3 (48%) in 1 pocket(s) |
| filament that would save | PASS | 2.80 cm3, 3.5 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.24 mm | (35.4, -20.2, 9.7) | 98 | 6.0 | 3.9 | 1.54 |
| 2 | wall | 0.24 mm | (-35.3, -20.3, 10.9) | 89 | 5.5 | 3.8 | 1.46 |
| 3 | taper | 0.24 mm | (-32.4, 7.4, 4.2) | 19 | 1.9 | 2.9 | 0.64 |
| 4 | taper | 0.24 mm | (32.3, 7.2, 4.5) | 19 | 1.7 | 3.1 | 0.56 |
| 5 | taper | 0.48 mm | (35.1, 4.7, 7.6) | 1 | 0.1 | 0.0 | 0.28 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
