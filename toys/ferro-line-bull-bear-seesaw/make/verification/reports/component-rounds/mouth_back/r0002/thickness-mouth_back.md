# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_mouth_back.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/mouth_back/r0002/thickness-mouth_back.md`

part_mouth_back.step.py: 24.52 cm3 solid, grid 0.147 mm (475x353x70), 370779 surface samples, thickness resolved to 0.074 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 0.5% of surface below (1834 of 370779 samples); thinnest 0.51 mm at (32.0, 20.5, 2.8) in 4 region(s); 4 wall(s) (widest band 3.49 mm); 557 more within measurement error of the limit |
| thickness distribution | PASS | median 9.55 mm, p95 69.09 mm, max 69.09 mm |
| hollowable at 1.20 mm wall | WARN | 15.76 of 24.52 cm3 (64%) in 1 pocket(s) |
| filament that would save | PASS | 2.36 cm3, 2.9 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.51 mm | (32.0, 20.5, 2.8) | 520 | 12.6 | 3.6 | 3.49 |
| 2 | wall | 0.51 mm | (-32.0, 20.4, 1.5) | 476 | 11.4 | 3.6 | 3.15 |
| 3 | wall | 0.59 mm | (26.6, 25.6, 2.8) | 426 | 10.2 | 3.4 | 2.96 |
| 4 | wall | 0.59 mm | (-27.5, 25.6, 0.2) | 412 | 9.9 | 3.5 | 2.87 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
