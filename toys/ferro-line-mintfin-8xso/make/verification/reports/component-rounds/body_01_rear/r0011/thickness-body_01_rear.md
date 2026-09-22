# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_01_rear.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_01_rear/r0011/thickness-body_01_rear.md`

part_body_01_rear.step.py: 5.64 cm3 solid, grid 0.133 mm (436x329x63), 244440 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.2% of surface below (520 of 244440 samples); thinnest 0.20 mm at (3.2, -12.0, 5.7) in 23 region(s); no region is a wall, 23 taper(s) at feature edges (0.22% of surface, budget 2%); 48 more within measurement error of the limit |
| thickness distribution | PASS | median 3.13 mm, p95 18.53 mm, max 57.47 mm |
| hollowable at 1.20 mm wall | WARN | 0.94 of 5.64 cm3 (17%) in 1 pocket(s) |
| filament that would save | PASS | 0.14 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.33 mm | (1.1, -3.9, 7.7) | 128 | 2.4 | 5.7 | 0.42 |
| 2 | taper | 0.20 mm | (2.8, -11.7, 7.7) | 119 | 2.3 | 5.5 | 0.41 |
| 3 | taper | 0.33 mm | (-2.0, -4.2, 7.7) | 117 | 2.2 | 5.7 | 0.38 |
| 4 | taper | 0.33 mm | (-3.6, -11.1, 7.7) | 105 | 1.9 | 5.6 | 0.35 |
| 5 | taper | 0.53 mm | (0.6, -1.2, 7.6) | 8 | 0.2 | 1.2 | 0.13 |
| 6 | taper | 0.73 mm | (0.5, -15.2, 7.5) | 7 | 0.1 | 1.2 | 0.12 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
