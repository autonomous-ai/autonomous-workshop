# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_circle_crater_moon.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/circle_crater_moon/r0001/thickness-circle_crater_moon.md`

part_circle_crater_moon.step.py: 2.73 cm3 solid, grid 0.133 mm (170x170x170), 90008 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.3% of surface below (181 of 90008 samples); thinnest 0.13 mm at (4.2, -3.5, 15.2) in 6 region(s); no region is a wall, 6 taper(s) at feature edges (0.33% of surface, budget 2%); 269 more within measurement error of the limit |
| thickness distribution | PASS | median 7.53 mm, p95 21.93 mm, max 22.07 mm |
| hollowable at 1.20 mm wall | WARN | 1.03 of 2.73 cm3 (38%) in 1 pocket(s) |
| filament that would save | PASS | 0.15 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (4.2, -3.5, 15.2) | 94 | 2.3 | 6.7 | 0.34 |
| 2 | taper | 0.73 mm | (-0.0, -8.4, 3.4) | 40 | 1.6 | 2.8 | 0.56 |
| 3 | taper | 0.73 mm | (0.0, 7.6, 3.4) | 42 | 1.6 | 2.8 | 0.56 |
| 4 | taper | 0.47 mm | (-0.4, -4.4, 13.0) | 3 | 0.1 | 0.2 | 0.25 |
| 5 | taper | 0.60 mm | (-1.5, -10.8, 3.7) | 1 | 0.0 | 0.0 | 0.21 |
| 6 | taper | 0.27 mm | (-0.5, -4.3, 14.2) | 1 | 0.0 | 0.0 | 0.17 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
