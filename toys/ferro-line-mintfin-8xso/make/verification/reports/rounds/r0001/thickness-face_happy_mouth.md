# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_face_happy_mouth.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/rounds/r0001/thickness-face_happy_mouth.md`

part_face_happy_mouth.step.py: 0.19 cm3 solid, grid 0.133 mm (131x72x20), 16983 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (7 of 16983 samples); thinnest 0.20 mm at (-7.1, 3.5, 2.0) in 7 region(s); no region is a wall, 7 taper(s) at feature edges (0.04% of surface, budget 2%); 1 more within measurement error of the limit |
| thickness distribution | PASS | median 1.93 mm, p95 8.00 mm, max 16.80 mm |
| hollowable at 1.20 mm wall | PASS | 0.00 of 0.19 cm3 (0%) in 0 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.20 mm | (-7.1, 3.5, 2.0) | 1 | 0.0 | 0.0 | 0.13 |
| 2 | taper | 0.67 mm | (5.4, -2.7, 0.1) | 1 | 0.0 | 0.0 | 0.13 |
| 3 | taper | 0.27 mm | (-5.7, 4.0, 0.1) | 1 | 0.0 | 0.0 | 0.13 |
| 4 | taper | 0.73 mm | (7.8, 3.2, 0.1) | 1 | 0.0 | 0.0 | 0.13 |
| 5 | taper | 0.47 mm | (-8.6, 1.7, 0.1) | 1 | 0.0 | 0.0 | 0.12 |
| 6 | taper | 0.67 mm | (-8.4, 1.0, 0.1) | 1 | 0.0 | 0.0 | 0.11 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
