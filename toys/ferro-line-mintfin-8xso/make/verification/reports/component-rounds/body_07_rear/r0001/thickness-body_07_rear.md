# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_07_rear.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_07_rear/r0001/thickness-body_07_rear.md`

part_body_07_rear.step.py: 0.89 cm3 solid, grid 0.133 mm (150x141x52), 51423 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 1.8% of surface below (888 of 51423 samples); thinnest 0.13 mm at (-3.5, -3.8, 6.2) in 19 region(s); no region is a wall, 19 taper(s) at feature edges (1.80% of surface, budget 2%); 116 more within measurement error of the limit |
| thickness distribution | PASS | median 3.47 mm, p95 7.07 mm, max 17.33 mm |
| hollowable at 1.20 mm wall | WARN | 0.08 of 0.89 cm3 (8%) in 3 pocket(s) |
| filament that would save | PASS | 0.01 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (-3.5, -3.8, 6.2) | 198 | 4.0 | 5.1 | 0.78 |
| 2 | taper | 0.13 mm | (-1.6, 1.8, 6.2) | 201 | 3.7 | 5.1 | 0.72 |
| 3 | taper | 0.13 mm | (3.9, -2.7, 6.2) | 186 | 3.7 | 5.0 | 0.73 |
| 4 | taper | 0.13 mm | (3.9, -1.1, 6.2) | 188 | 3.6 | 5.1 | 0.71 |
| 5 | taper | 0.13 mm | (-7.7, -1.4, 3.2) | 46 | 1.1 | 2.2 | 0.52 |
| 6 | taper | 0.13 mm | (7.8, -1.9, 3.1) | 40 | 0.9 | 1.9 | 0.47 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
