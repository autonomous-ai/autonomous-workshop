# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_face_nostril.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/face_nostril/r0001/thickness-face_nostril.md`

part_face_nostril.step.py: 0.00 cm3 solid, grid 0.133 mm (17x17x11), 392 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 25.8% of surface below (113 of 392 samples); thinnest 0.73 mm at (0.4, -0.7, 0.8) in 1 region(s); 1 wall(s) (widest band 0.97 mm); 115 more within measurement error of the limit |
| thickness distribution | PASS | median 0.80 mm, p95 1.60 mm, max 1.67 mm |
| hollowable at 1.20 mm wall | PASS | 0.00 of 0.00 cm3 (0%) in 0 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.73 mm | (0.4, -0.7, 0.8) | 113 | 2.0 | 2.0 | 0.97 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
