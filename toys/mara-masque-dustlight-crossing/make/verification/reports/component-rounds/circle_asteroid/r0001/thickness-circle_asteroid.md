# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_circle_asteroid.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/circle_asteroid/r0001/thickness-circle_asteroid.md`

part_circle_asteroid.step.py: 2.97 cm3 solid, grid 0.133 mm (170x170x155), 87478 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 0.5% of surface below (374 of 87478 samples); thinnest 0.13 mm at (-0.9, -7.3, 9.8) in 8 region(s); 1 wall(s) (widest band 0.97 mm), 7 taper(s) at feature edges (0.18% of surface, budget 2%); 252 more within measurement error of the limit |
| thickness distribution | PASS | median 11.73 mm, p95 21.93 mm, max 22.07 mm |
| hollowable at 1.20 mm wall | WARN | 1.26 of 2.97 cm3 (42%) in 1 pocket(s) |
| filament that would save | PASS | 0.19 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.13 mm | (-0.9, -7.3, 9.8) | 280 | 5.4 | 5.5 | 0.97 |
| 2 | taper | 0.73 mm | (1.1, -8.4, 3.4) | 39 | 1.3 | 2.5 | 0.52 |
| 3 | taper | 0.73 mm | (-0.9, 7.6, 3.4) | 32 | 1.3 | 2.5 | 0.51 |
| 4 | taper | 0.20 mm | (2.0, -5.1, 16.2) | 12 | 0.2 | 1.8 | 0.13 |
| 5 | taper | 0.13 mm | (3.0, -5.2, 8.1) | 5 | 0.1 | 0.5 | 0.12 |
| 6 | taper | 0.40 mm | (1.9, -5.1, 7.0) | 4 | 0.0 | 0.1 | 0.37 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
