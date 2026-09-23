# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_02_rear.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_02_rear/r0004/thickness-body_02_rear.md`

part_body_02_rear.step.py: 5.89 cm3 solid, grid 0.133 mm (452x334x66), 257010 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.3% of surface below (814 of 257010 samples); thinnest 0.13 mm at (-3.0, -12.4, 6.4) in 25 region(s); no region is a wall, 25 taper(s) at feature edges (0.35% of surface, budget 2%); 184 more within measurement error of the limit |
| thickness distribution | PASS | median 3.13 mm, p95 18.87 mm, max 59.60 mm |
| hollowable at 1.20 mm wall | WARN | 0.97 of 5.89 cm3 (16%) in 1 pocket(s) |
| filament that would save | PASS | 0.15 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (-4.0, -10.1, 8.1) | 196 | 4.0 | 5.5 | 0.73 |
| 2 | taper | 0.13 mm | (-1.7, -4.9, 8.1) | 199 | 3.9 | 5.4 | 0.72 |
| 3 | taper | 0.13 mm | (3.3, -11.4, 8.1) | 188 | 3.9 | 5.6 | 0.70 |
| 4 | taper | 0.13 mm | (1.7, -5.0, 8.1) | 169 | 3.2 | 5.6 | 0.57 |
| 5 | taper | 0.73 mm | (-0.3, -14.7, 1.6) | 16 | 0.3 | 0.8 | 0.37 |
| 6 | taper | 0.20 mm | (-0.6, -2.0, 3.8) | 7 | 0.1 | 0.7 | 0.21 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
