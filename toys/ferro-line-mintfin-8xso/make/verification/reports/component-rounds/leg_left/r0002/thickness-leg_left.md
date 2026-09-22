# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_leg_left.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/leg_left/r0002/thickness-leg_left.md`

part_leg_left.step.py: 5.28 cm3 solid, grid 0.133 mm (211x200x147), 110608 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 1.6% of surface below (1624 of 110608 samples); thinnest 0.13 mm at (8.4, -8.0, 0.9) in 6 region(s); 3 wall(s) (widest band 1.87 mm), 3 taper(s) at feature edges (0.03% of surface, budget 2%); 204 more within measurement error of the limit |
| thickness distribution | PASS | median 13.07 mm, p95 22.60 mm, max 24.20 mm |
| hollowable at 1.20 mm wall | WARN | 3.16 of 5.28 cm3 (60%) in 1 pocket(s) |
| filament that would save | PASS | 0.47 cm3, 0.6 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.13 mm | (8.4, -8.0, 0.9) | 810 | 16.3 | 8.7 | 1.87 |
| 2 | wall | 0.13 mm | (-8.3, -12.2, 0.8) | 457 | 9.8 | 7.1 | 1.37 |
| 3 | wall | 0.13 mm | (2.2, -12.2, 4.5) | 325 | 6.7 | 6.8 | 0.98 |
| 4 | taper | 0.13 mm | (11.9, 9.3, 19.0) | 26 | 0.6 | 3.3 | 0.17 |
| 5 | taper | 0.40 mm | (9.3, 11.4, 19.0) | 4 | 0.1 | 0.4 | 0.21 |
| 6 | taper | 0.27 mm | (8.2, 11.8, 19.0) | 2 | 0.0 | 0.1 | 0.25 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
