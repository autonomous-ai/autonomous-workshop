# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_circle_asteroid.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/thickness-circle_asteroid.md`

part_circle_asteroid.step.py: 2.98 cm3 solid, grid 0.133 mm (170x170x155), 86393 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.4% of surface below (162 of 86393 samples); thinnest 0.13 mm at (2.8, -5.5, 8.6) in 8 region(s); no region is a wall, 7 taper(s) at feature edges and 1 spot(s) too small to be a wall (0.37% of surface, budget 2%); 203 more within measurement error of the limit |
| thickness distribution | PASS | median 11.87 mm, p95 21.93 mm, max 22.07 mm |
| hollowable at 1.20 mm wall | WARN | 1.27 of 2.98 cm3 (43%) in 1 pocket(s) |
| filament that would save | PASS | 0.19 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.73 mm | (-0.1, -10.4, 3.4) | 39 | 1.6 | 2.8 | 0.56 |
| 2 | taper | 0.73 mm | (-1.2, 9.6, 3.5) | 45 | 1.6 | 2.9 | 0.55 |
| 3 | taper | 0.20 mm | (-3.4, -5.5, 12.2) | 34 | 1.1 | 2.2 | 0.49 |
| 4 | taper | 0.73 mm | (-0.0, 5.4, 3.3) | 20 | 0.8 | 1.7 | 0.49 |
| 5 | taper | 0.73 mm | (0.4, -4.6, 3.3) | 11 | 0.5 | 0.8 | 0.64 |
| 6 | taper | 0.13 mm | (2.8, -5.5, 8.6) | 9 | 0.3 | 1.3 | 0.27 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
