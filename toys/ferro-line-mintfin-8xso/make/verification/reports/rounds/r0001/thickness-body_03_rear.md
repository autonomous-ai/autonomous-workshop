# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_03_rear.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/rounds/r0001/thickness-body_03_rear.md`

part_body_03_rear.step.py: 5.08 cm3 solid, grid 0.133 mm (403x310x66), 222173 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.4% of surface below (768 of 222173 samples); thinnest 0.13 mm at (-0.6, -4.1, 8.1) in 18 region(s); no region is a wall, 18 taper(s) at feature edges (0.38% of surface, budget 2%); 125 more within measurement error of the limit |
| thickness distribution | PASS | median 3.13 mm, p95 19.67 mm, max 53.07 mm |
| hollowable at 1.20 mm wall | WARN | 0.84 of 5.08 cm3 (17%) in 1 pocket(s) |
| filament that would save | PASS | 0.13 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (4.1, -9.1, 8.1) | 207 | 4.3 | 5.4 | 0.79 |
| 2 | taper | 0.13 mm | (-3.9, -9.8, 8.1) | 173 | 3.7 | 5.4 | 0.69 |
| 3 | taper | 0.13 mm | (-0.6, -4.1, 8.1) | 184 | 3.5 | 5.5 | 0.64 |
| 4 | taper | 0.13 mm | (2.3, -4.8, 8.1) | 178 | 3.4 | 5.5 | 0.61 |
| 5 | taper | 0.47 mm | (0.4, -16.2, 3.0) | 3 | 0.1 | 1.3 | 0.06 |
| 6 | taper | 0.47 mm | (-0.5, -1.6, 8.1) | 3 | 0.1 | 0.1 | 0.47 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
