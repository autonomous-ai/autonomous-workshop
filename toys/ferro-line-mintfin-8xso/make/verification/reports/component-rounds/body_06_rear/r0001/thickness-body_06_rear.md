# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_06_rear.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_06_rear/r0001/thickness-body_06_rear.md`

part_body_06_rear.step.py: 1.63 cm3 solid, grid 0.133 mm (208x178x56), 80720 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 1.0% of surface below (789 of 80720 samples); thinnest 0.13 mm at (-1.3, -0.5, 6.7) in 18 region(s); no region is a wall, 18 taper(s) at feature edges (1.01% of surface, budget 2%); 45 more within measurement error of the limit |
| thickness distribution | PASS | median 3.47 mm, p95 12.87 mm, max 27.13 mm |
| hollowable at 1.20 mm wall | WARN | 0.24 of 1.63 cm3 (15%) in 1 pocket(s) |
| filament that would save | PASS | 0.04 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (-1.3, -0.5, 6.7) | 199 | 3.8 | 5.2 | 0.73 |
| 2 | taper | 0.13 mm | (0.8, -0.4, 6.7) | 200 | 3.7 | 5.2 | 0.72 |
| 3 | taper | 0.13 mm | (3.9, -5.1, 6.7) | 186 | 3.6 | 5.1 | 0.70 |
| 4 | taper | 0.13 mm | (-3.4, -6.2, 6.8) | 173 | 3.5 | 5.2 | 0.67 |
| 5 | taper | 0.67 mm | (-6.5, -3.7, 3.6) | 10 | 0.2 | 2.7 | 0.08 |
| 6 | taper | 0.47 mm | (3.1, -7.4, 3.5) | 2 | 0.1 | 0.4 | 0.18 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
