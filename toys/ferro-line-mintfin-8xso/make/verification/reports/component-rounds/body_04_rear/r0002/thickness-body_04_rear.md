# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_04_rear.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_04_rear/r0002/thickness-body_04_rear.md`

part_body_04_rear.step.py: 4.37 cm3 solid, grid 0.133 mm (356x293x66), 193759 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.4% of surface below (784 of 193759 samples); thinnest 0.13 mm at (-0.6, -3.9, 8.1) in 24 region(s); no region is a wall, 24 taper(s) at feature edges (0.44% of surface, budget 2%); 110 more within measurement error of the limit |
| thickness distribution | PASS | median 3.13 mm, p95 17.33 mm, max 46.87 mm |
| hollowable at 1.20 mm wall | WARN | 0.70 of 4.37 cm3 (16%) in 1 pocket(s) |
| filament that would save | PASS | 0.11 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (-3.5, -10.1, 8.1) | 195 | 4.1 | 5.2 | 0.80 |
| 2 | taper | 0.13 mm | (4.0, -8.9, 8.1) | 187 | 3.7 | 5.3 | 0.70 |
| 3 | taper | 0.13 mm | (1.9, -4.4, 8.1) | 181 | 3.4 | 5.2 | 0.65 |
| 4 | taper | 0.13 mm | (-0.6, -3.9, 8.1) | 164 | 3.3 | 5.2 | 0.63 |
| 5 | taper | 0.73 mm | (-0.5, -14.6, 3.8) | 10 | 0.2 | 1.7 | 0.13 |
| 6 | taper | 0.53 mm | (0.2, -15.7, 2.9) | 9 | 0.2 | 0.7 | 0.29 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
