# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_02_rear.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_02_rear/r0003/thickness-body_02_rear.md`

part_body_02_rear.step.py: 5.92 cm3 solid, grid 0.133 mm (452x334x66), 256306 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.3% of surface below (767 of 256306 samples); thinnest 0.13 mm at (-2.2, -5.2, 8.1) in 22 region(s); no region is a wall, 22 taper(s) at feature edges (0.32% of surface, budget 2%); 176 more within measurement error of the limit |
| thickness distribution | PASS | median 3.13 mm, p95 20.87 mm, max 59.60 mm |
| hollowable at 1.20 mm wall | WARN | 1.00 of 5.92 cm3 (17%) in 1 pocket(s) |
| filament that would save | PASS | 0.15 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (3.2, -11.5, 8.1) | 195 | 3.9 | 5.6 | 0.70 |
| 2 | taper | 0.13 mm | (2.0, -5.1, 8.1) | 182 | 3.5 | 5.5 | 0.63 |
| 3 | taper | 0.13 mm | (-1.2, -12.8, 8.1) | 166 | 3.4 | 5.4 | 0.63 |
| 4 | taper | 0.13 mm | (-2.2, -5.2, 8.1) | 164 | 3.2 | 5.4 | 0.59 |
| 5 | taper | 0.73 mm | (-0.3, -14.6, 1.6) | 15 | 0.3 | 0.8 | 0.37 |
| 6 | taper | 0.67 mm | (-0.5, -2.1, 8.2) | 10 | 0.2 | 2.2 | 0.10 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
