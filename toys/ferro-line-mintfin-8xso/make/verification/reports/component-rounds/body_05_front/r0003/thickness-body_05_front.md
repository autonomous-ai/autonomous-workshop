# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_05_front.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_05_front/r0003/thickness-body_05_front.md`

part_body_05_front.step.py: 2.98 cm3 solid, grid 0.133 mm (276x232x86), 123651 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 0.9% of surface below (1027 of 123651 samples); thinnest 0.13 mm at (-0.2, 10.0, 0.0) in 9 region(s); 1 wall(s) (widest band 2.15 mm), 8 taper(s) at feature edges (0.12% of surface, budget 2%); 280 more within measurement error of the limit |
| thickness distribution | PASS | median 3.47 mm, p95 12.73 mm, max 36.20 mm |
| hollowable at 1.20 mm wall | WARN | 0.67 of 2.98 cm3 (22%) in 1 pocket(s) |
| filament that would save | PASS | 0.10 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.13 mm | (-0.2, 10.0, 0.0) | 922 | 17.5 | 8.1 | 2.15 |
| 2 | taper | 0.13 mm | (-1.7, 12.0, 3.4) | 91 | 2.2 | 6.7 | 0.33 |
| 3 | taper | 0.13 mm | (2.3, 11.2, 2.3) | 1 | 0.1 | 0.0 | 0.68 |
| 4 | taper | 0.33 mm | (7.0, 3.1, 3.4) | 5 | 0.1 | 1.0 | 0.07 |
| 5 | taper | 0.27 mm | (4.2, 9.9, 2.0) | 1 | 0.1 | 0.0 | 0.57 |
| 6 | taper | 0.13 mm | (-4.8, 9.4, 2.1) | 1 | 0.1 | 0.0 | 0.51 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
