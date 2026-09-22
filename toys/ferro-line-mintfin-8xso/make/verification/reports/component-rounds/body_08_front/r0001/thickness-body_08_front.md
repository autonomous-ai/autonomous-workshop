# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_08_front.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_08_front/r0001/thickness-body_08_front.md`

part_body_08_front.step.py: 0.74 cm3 solid, grid 0.133 mm (107x141x67), 34799 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 3.3% of surface below (982 of 34799 samples); thinnest 0.13 mm at (-5.9, -3.2, 1.9) in 2 region(s); 2 wall(s) (widest band 1.49 mm); 15 more within measurement error of the limit |
| thickness distribution | PASS | median 6.80 mm, p95 13.67 mm, max 17.60 mm |
| hollowable at 1.20 mm wall | WARN | 0.18 of 0.74 cm3 (25%) in 2 pocket(s) |
| filament that would save | PASS | 0.03 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.13 mm | (-5.9, -3.2, 1.9) | 497 | 10.5 | 7.2 | 1.47 |
| 2 | wall | 0.13 mm | (6.0, -3.3, 0.8) | 485 | 10.5 | 7.0 | 1.49 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
