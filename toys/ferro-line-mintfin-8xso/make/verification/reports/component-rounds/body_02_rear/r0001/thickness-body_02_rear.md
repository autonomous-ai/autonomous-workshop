# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_02_rear.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_02_rear/r0001/thickness-body_02_rear.md`

part_body_02_rear.step.py: 6.33 cm3 solid, grid 0.133 mm (452x343x66), 272574 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 0.5% of surface below (1263 of 272574 samples); thinnest 0.13 mm at (-0.4, -21.3, 2.0) in 24 region(s); 2 wall(s) (widest band 1.68 mm), 22 taper(s) at feature edges (0.32% of surface, budget 2%); 475 more within measurement error of the limit |
| thickness distribution | PASS | median 3.13 mm, p95 8.13 mm, max 59.60 mm |
| hollowable at 1.20 mm wall | WARN | 1.06 of 6.33 cm3 (17%) in 1 pocket(s) |
| filament that would save | PASS | 0.16 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.13 mm | (-0.4, -21.3, 2.0) | 392 | 7.4 | 4.4 | 1.68 |
| 2 | taper | 0.13 mm | (-2.0, -12.5, 8.1) | 179 | 3.8 | 5.3 | 0.72 |
| 3 | taper | 0.13 mm | (3.3, -11.4, 8.1) | 186 | 3.8 | 5.4 | 0.70 |
| 4 | taper | 0.13 mm | (-0.8, -4.7, 8.1) | 183 | 3.7 | 5.4 | 0.68 |
| 5 | taper | 0.13 mm | (4.2, -8.0, 8.2) | 173 | 3.3 | 5.5 | 0.61 |
| 6 | wall | 0.73 mm | (-0.4, -8.2, 0.8) | 95 | 1.7 | 1.9 | 0.85 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
