# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_square_asteroid.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/square_asteroid/r0001/thickness-square_asteroid.md`

part_square_asteroid.step.py: 3.25 cm3 solid, grid 0.133 mm (170x170x155), 97289 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.3% of surface below (183 of 97289 samples); thinnest 0.13 mm at (-2.6, -5.6, 13.0) in 9 region(s); no region is a wall, 8 taper(s) at feature edges and 1 spot(s) too small to be a wall (0.35% of surface, budget 2%); 199 more within measurement error of the limit |
| thickness distribution | PASS | median 11.33 mm, p95 22.00 mm, max 26.93 mm |
| hollowable at 1.20 mm wall | WARN | 1.33 of 3.25 cm3 (41%) in 1 pocket(s) |
| filament that would save | PASS | 0.20 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.73 mm | (-1.1, 9.6, 3.5) | 47 | 1.6 | 2.9 | 0.54 |
| 2 | taper | 0.73 mm | (1.6, -10.4, 3.5) | 37 | 1.5 | 3.0 | 0.51 |
| 3 | taper | 0.13 mm | (-2.6, -5.6, 13.0) | 31 | 1.0 | 1.9 | 0.54 |
| 4 | taper | 0.73 mm | (0.4, 5.4, 3.3) | 29 | 1.0 | 1.6 | 0.59 |
| 5 | taper | 0.73 mm | (0.5, -4.6, 3.4) | 19 | 0.6 | 0.9 | 0.69 |
| 6 | taper | 0.13 mm | (2.8, -5.4, 8.8) | 13 | 0.6 | 1.1 | 0.50 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
