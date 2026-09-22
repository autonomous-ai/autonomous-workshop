# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_03_rear.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_03_rear/r0001/thickness-body_03_rear.md`

part_body_03_rear.step.py: 5.28 cm3 solid, grid 0.133 mm (403x319x66), 230998 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 0.6% of surface below (1256 of 230998 samples); thinnest 0.13 mm at (1.1, -20.3, 1.7) in 26 region(s); 1 wall(s) (widest band 1.74 mm), 25 taper(s) at feature edges (0.40% of surface, budget 2%); 443 more within measurement error of the limit |
| thickness distribution | PASS | median 3.13 mm, p95 8.13 mm, max 53.07 mm |
| hollowable at 1.20 mm wall | WARN | 0.86 of 5.28 cm3 (16%) in 1 pocket(s) |
| filament that would save | PASS | 0.13 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.13 mm | (1.1, -20.3, 1.7) | 393 | 7.4 | 4.3 | 1.74 |
| 2 | taper | 0.13 mm | (-3.4, -10.8, 8.1) | 195 | 3.9 | 5.4 | 0.73 |
| 3 | taper | 0.13 mm | (4.1, -9.2, 8.1) | 198 | 3.8 | 5.4 | 0.71 |
| 4 | taper | 0.13 mm | (4.2, -7.6, 8.1) | 185 | 3.7 | 5.3 | 0.68 |
| 5 | taper | 0.13 mm | (-1.0, -4.2, 8.1) | 177 | 3.4 | 5.4 | 0.64 |
| 6 | taper | 0.73 mm | (-0.2, -7.9, 0.8) | 51 | 0.9 | 1.5 | 0.61 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
