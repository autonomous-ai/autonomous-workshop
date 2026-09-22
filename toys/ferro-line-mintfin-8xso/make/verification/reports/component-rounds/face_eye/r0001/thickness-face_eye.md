# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_face_eye.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/face_eye/r0001/thickness-face_eye.md`

part_face_eye.step.py: 0.73 cm3 solid, grid 0.133 mm (117x117x55), 27922 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 1.9% of surface below (439 of 27922 samples); thinnest 0.13 mm at (-3.4, 2.8, 5.2) in 3 region(s); no region is a wall, 3 taper(s) at feature edges (1.87% of surface, budget 2%); 106 more within measurement error of the limit |
| thickness distribution | PASS | median 5.47 mm, p95 6.67 mm, max 6.80 mm |
| hollowable at 1.20 mm wall | WARN | 0.26 of 0.73 cm3 (35%) in 1 pocket(s) |
| filament that would save | PASS | 0.04 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (-6.7, 3.3, 0.1) | 370 | 7.9 | 21.1 | 0.37 |
| 2 | taper | 0.13 mm | (-1.5, 4.0, 5.4) | 38 | 0.8 | 2.1 | 0.37 |
| 3 | taper | 0.13 mm | (-3.4, 2.8, 5.2) | 31 | 0.7 | 2.0 | 0.33 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
