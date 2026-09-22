# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_04_rear.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_04_rear/r0004/thickness-body_04_rear.md`

part_body_04_rear.step.py: 4.33 cm3 solid, grid 0.133 mm (356x293x66), 192290 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (78 of 192290 samples); thinnest 0.20 mm at (-0.5, -1.4, 8.1) in 30 region(s); no region is a wall, 30 taper(s) at feature edges (0.05% of surface, budget 2%); 60 more within measurement error of the limit |
| thickness distribution | PASS | median 3.13 mm, p95 16.93 mm, max 46.87 mm |
| hollowable at 1.20 mm wall | WARN | 0.69 of 4.33 cm3 (16%) in 1 pocket(s) |
| filament that would save | PASS | 0.10 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.20 mm | (6.7, -8.6, 8.0) | 13 | 0.3 | 2.1 | 0.13 |
| 2 | taper | 0.47 mm | (0.1, -15.9, 3.0) | 8 | 0.2 | 0.7 | 0.25 |
| 3 | taper | 0.73 mm | (-0.5, -14.6, 4.7) | 6 | 0.1 | 1.4 | 0.09 |
| 4 | taper | 0.73 mm | (0.5, -14.6, 6.8) | 5 | 0.1 | 1.8 | 0.06 |
| 5 | taper | 0.20 mm | (-6.7, -7.5, 3.3) | 5 | 0.1 | 0.5 | 0.17 |
| 6 | taper | 0.53 mm | (6.7, -8.6, 5.3) | 3 | 0.1 | 0.7 | 0.12 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
