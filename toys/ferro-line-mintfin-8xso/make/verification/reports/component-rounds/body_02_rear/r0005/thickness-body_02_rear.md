# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_02_rear.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_02_rear/r0005/thickness-body_02_rear.md`

part_body_02_rear.step.py: 5.90 cm3 solid, grid 0.133 mm (452x334x66), 256952 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 0.4% of surface below (902 of 256952 samples); thinnest 0.13 mm at (-2.6, -5.5, 8.1) in 27 region(s); 1 wall(s) (widest band 1.31 mm), 26 taper(s) at feature edges (0.33% of surface, budget 2%); 192 more within measurement error of the limit |
| thickness distribution | PASS | median 3.13 mm, p95 19.67 mm, max 59.60 mm |
| hollowable at 1.20 mm wall | WARN | 0.98 of 5.90 cm3 (17%) in 1 pocket(s) |
| filament that would save | PASS | 0.15 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (-3.9, -10.4, 8.1) | 187 | 3.7 | 5.5 | 0.68 |
| 2 | taper | 0.13 mm | (-2.6, -5.5, 8.1) | 189 | 3.7 | 5.4 | 0.68 |
| 3 | taper | 0.13 mm | (3.2, -11.5, 8.1) | 172 | 3.6 | 5.4 | 0.65 |
| 4 | taper | 0.13 mm | (1.5, -4.9, 8.1) | 166 | 3.2 | 5.4 | 0.60 |
| 5 | wall | 0.13 mm | (0.2, -14.0, 1.5) | 124 | 2.6 | 2.0 | 1.31 |
| 6 | taper | 0.67 mm | (-0.5, -2.1, 7.4) | 10 | 0.2 | 2.1 | 0.11 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
