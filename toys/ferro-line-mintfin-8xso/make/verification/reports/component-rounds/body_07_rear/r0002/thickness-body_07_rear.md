# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_07_rear.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_07_rear/r0002/thickness-body_07_rear.md`

part_body_07_rear.step.py: 0.94 cm3 solid, grid 0.133 mm (150x141x57), 53966 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.3% of surface below (138 of 53966 samples); thinnest 0.13 mm at (-7.7, -2.3, 3.1) in 22 region(s); no region is a wall, 22 taper(s) at feature edges (0.29% of surface, budget 2%); 26 more within measurement error of the limit |
| thickness distribution | PASS | median 3.40 mm, p95 6.93 mm, max 17.33 mm |
| hollowable at 1.20 mm wall | WARN | 0.08 of 0.94 cm3 (8%) in 3 pocket(s) |
| filament that would save | PASS | 0.01 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (-7.7, -2.3, 3.1) | 49 | 1.1 | 2.5 | 0.44 |
| 2 | taper | 0.13 mm | (7.8, -1.6, 3.2) | 34 | 0.8 | 2.0 | 0.37 |
| 3 | taper | 0.60 mm | (3.8, -3.0, 6.9) | 8 | 0.2 | 2.1 | 0.07 |
| 4 | taper | 0.73 mm | (-3.4, 0.5, 6.9) | 7 | 0.1 | 2.0 | 0.07 |
| 5 | taper | 0.33 mm | (-6.6, -2.4, 6.5) | 6 | 0.1 | 0.5 | 0.24 |
| 6 | taper | 0.67 mm | (-6.5, -1.3, 5.1) | 4 | 0.1 | 0.7 | 0.14 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
