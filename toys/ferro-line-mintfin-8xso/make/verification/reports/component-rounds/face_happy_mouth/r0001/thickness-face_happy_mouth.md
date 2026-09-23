# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_face_happy_mouth.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/face_happy_mouth/r0001/thickness-face_happy_mouth.md`

part_face_happy_mouth.step.py: 0.19 cm3 solid, grid 0.133 mm (131x72x20), 16972 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 5.0% of surface below (772 of 16972 samples); thinnest 0.33 mm at (0.8, -5.0, 1.8) in 4 region(s); 1 wall(s) (widest band 1.60 mm), 3 taper(s) at feature edges (0.02% of surface, budget 2%); 26 more within measurement error of the limit |
| thickness distribution | PASS | median 1.93 mm, p95 8.00 mm, max 16.80 mm |
| hollowable at 1.20 mm wall | PASS | 0.00 of 0.19 cm3 (0%) in 0 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.33 mm | (0.8, -5.0, 1.8) | 767 | 16.0 | 9.9 | 1.60 |
| 2 | taper | 0.53 mm | (-8.5, 1.4, 0.1) | 3 | 0.0 | 0.5 | 0.09 |
| 3 | taper | 0.60 mm | (6.1, 3.9, 0.1) | 1 | 0.0 | 0.0 | 0.13 |
| 4 | taper | 0.47 mm | (8.2, 2.2, 0.1) | 1 | 0.0 | 0.0 | 0.11 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
