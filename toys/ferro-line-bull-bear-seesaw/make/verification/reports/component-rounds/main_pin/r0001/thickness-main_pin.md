# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_main_pin.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/main_pin/r0001/thickness-main_pin.md`

part_main_pin.step.py: 0.89 cm3 solid, grid 0.133 mm (80x80x219), 42031 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 1.7% of surface below (692 of 42031 samples); thinnest 0.13 mm at (1.6, -2.6, 24.5) in 4 region(s); 4 wall(s) (widest band 1.31 mm); 90 more within measurement error of the limit |
| thickness distribution | PASS | median 5.93 mm, p95 23.73 mm, max 28.53 mm |
| hollowable at 1.20 mm wall | WARN | 0.21 of 0.89 cm3 (24%) in 1 pocket(s) |
| filament that would save | PASS | 0.03 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.13 mm | (1.6, -2.6, 24.5) | 199 | 3.8 | 2.9 | 1.31 |
| 2 | wall | 0.13 mm | (1.5, 2.6, 25.1) | 190 | 3.6 | 2.9 | 1.25 |
| 3 | wall | 0.13 mm | (-1.4, 2.6, 24.8) | 157 | 3.0 | 2.9 | 1.04 |
| 4 | wall | 0.13 mm | (-1.4, -2.6, 24.0) | 146 | 2.8 | 2.9 | 0.98 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
