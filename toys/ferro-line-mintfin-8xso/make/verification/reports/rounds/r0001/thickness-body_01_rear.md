# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_01_rear.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/rounds/r0001/thickness-body_01_rear.md`

part_body_01_rear.step.py: 5.60 cm3 solid, grid 0.133 mm (436x329x63), 243241 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (62 of 243241 samples); thinnest 0.13 mm at (7.1, -8.9, 7.6) in 22 region(s); no region is a wall, 22 taper(s) at feature edges (0.03% of surface, budget 2%); 5 more within measurement error of the limit |
| thickness distribution | PASS | median 3.13 mm, p95 20.27 mm, max 57.47 mm |
| hollowable at 1.20 mm wall | WARN | 0.94 of 5.60 cm3 (17%) in 1 pocket(s) |
| filament that would save | PASS | 0.14 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.73 mm | (-0.5, -1.3, 7.7) | 12 | 0.2 | 3.1 | 0.08 |
| 2 | taper | 0.73 mm | (-4.4, -7.4, 7.7) | 6 | 0.1 | 2.0 | 0.06 |
| 3 | taper | 0.40 mm | (0.6, -15.4, 3.5) | 5 | 0.1 | 0.4 | 0.25 |
| 4 | taper | 0.73 mm | (2.6, -12.0, 7.7) | 4 | 0.1 | 0.8 | 0.10 |
| 5 | taper | 0.60 mm | (3.2, -5.2, 7.7) | 4 | 0.1 | 0.4 | 0.20 |
| 6 | taper | 0.73 mm | (-3.2, -11.5, 7.7) | 4 | 0.1 | 1.2 | 0.06 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
