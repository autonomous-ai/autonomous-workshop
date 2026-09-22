# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_04_rear.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_04_rear/r0001/thickness-body_04_rear.md`

part_body_04_rear.step.py: 4.45 cm3 solid, grid 0.133 mm (356x301x66), 197431 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 0.7% of surface below (1241 of 197431 samples); thinnest 0.13 mm at (3.2, -4.8, 6.5) in 24 region(s); 1 wall(s) (widest band 1.64 mm), 23 taper(s) at feature edges (0.44% of surface, budget 2%); 123 more within measurement error of the limit |
| thickness distribution | PASS | median 3.13 mm, p95 9.53 mm, max 46.87 mm |
| hollowable at 1.20 mm wall | WARN | 0.71 of 4.45 cm3 (16%) in 1 pocket(s) |
| filament that would save | PASS | 0.11 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.13 mm | (1.5, -19.7, 1.3) | 422 | 8.0 | 4.9 | 1.64 |
| 2 | taper | 0.13 mm | (3.8, -9.5, 8.1) | 198 | 3.9 | 5.3 | 0.75 |
| 3 | taper | 0.13 mm | (-3.4, -10.5, 8.2) | 185 | 3.7 | 5.3 | 0.70 |
| 4 | taper | 0.13 mm | (-1.0, -4.0, 8.1) | 195 | 3.7 | 5.4 | 0.68 |
| 5 | taper | 0.13 mm | (4.0, -7.4, 8.1) | 188 | 3.6 | 5.3 | 0.67 |
| 6 | taper | 0.60 mm | (-0.1, -15.7, 2.8) | 5 | 0.1 | 0.7 | 0.20 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
