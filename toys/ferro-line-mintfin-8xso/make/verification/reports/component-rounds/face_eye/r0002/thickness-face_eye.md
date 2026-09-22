# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_face_eye.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/face_eye/r0002/thickness-face_eye.md`

part_face_eye.step.py: 0.77 cm3 solid, grid 0.133 mm (117x117x55), 28507 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.3% of surface below (85 of 28507 samples); thinnest 0.13 mm at (-1.8, 4.0, 5.4) in 1 region(s); no region is a wall, 1 taper(s) at feature edges (0.32% of surface, budget 2%); 3 more within measurement error of the limit |
| thickness distribution | PASS | median 5.73 mm, p95 14.93 mm, max 15.07 mm |
| hollowable at 1.20 mm wall | WARN | 0.28 of 0.77 cm3 (36%) in 1 pocket(s) |
| filament that would save | PASS | 0.04 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (-1.8, 4.0, 5.4) | 85 | 1.6 | 4.2 | 0.39 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
