# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_circle_red_giant.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/circle_red_giant/r0001/thickness-circle_red_giant.md`

part_circle_red_giant.step.py: 4.93 cm3 solid, grid 0.133 mm (170x170x245), 116977 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.2% of surface below (133 of 116977 samples); thinnest 0.73 mm at (0.9, -10.4, 3.5) in 4 region(s); no region is a wall, 4 taper(s) at feature edges (0.25% of surface, budget 2%); 228 more within measurement error of the limit |
| thickness distribution | PASS | median 14.20 mm, p95 22.00 mm, max 32.00 mm |
| hollowable at 1.20 mm wall | WARN | 2.56 of 4.93 cm3 (52%) in 1 pocket(s) |
| filament that would save | PASS | 0.38 cm3, 0.5 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.73 mm | (1.1, -4.6, 3.4) | 34 | 1.4 | 2.5 | 0.57 |
| 2 | taper | 0.73 mm | (-1.1, 9.6, 3.5) | 34 | 1.4 | 2.4 | 0.57 |
| 3 | taper | 0.73 mm | (-0.9, 5.4, 3.3) | 31 | 1.4 | 2.2 | 0.62 |
| 4 | taper | 0.73 mm | (0.9, -10.4, 3.5) | 34 | 1.4 | 2.6 | 0.51 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
