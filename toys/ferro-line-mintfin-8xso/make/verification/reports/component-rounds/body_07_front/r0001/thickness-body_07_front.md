# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_07_front.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_07_front/r0001/thickness-body_07_front.md`

part_body_07_front.step.py: 0.96 cm3 solid, grid 0.133 mm (150x141x71), 50539 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 2.9% of surface below (1368 of 50539 samples); thinnest 0.13 mm at (4.8, -8.3, 1.6) in 3 region(s); 3 wall(s) (widest band 2.04 mm); 95 more within measurement error of the limit |
| thickness distribution | PASS | median 3.47 mm, p95 9.67 mm, max 19.40 mm |
| hollowable at 1.20 mm wall | WARN | 0.19 of 0.96 cm3 (19%) in 2 pocket(s) |
| filament that would save | PASS | 0.03 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.13 mm | (1.1, 1.5, 1.5) | 530 | 9.8 | 4.8 | 2.04 |
| 2 | wall | 0.13 mm | (4.8, -8.3, 1.6) | 416 | 8.8 | 8.0 | 1.09 |
| 3 | wall | 0.13 mm | (-4.8, -8.3, 1.7) | 422 | 8.7 | 8.3 | 1.05 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
