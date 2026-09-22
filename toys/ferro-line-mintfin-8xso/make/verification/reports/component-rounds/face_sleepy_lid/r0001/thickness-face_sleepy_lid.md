# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_face_sleepy_lid.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/face_sleepy_lid/r0001/thickness-face_sleepy_lid.md`

part_face_sleepy_lid.step.py: 0.02 cm3 solid, grid 0.133 mm (110x35x14), 3419 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 3.9% of surface below (103 of 3419 samples); thinnest 0.13 mm at (-6.8, 2.2, 0.1) in 2 region(s); no region is a wall, 0 taper(s) at feature edges and 2 spot(s) too small to be a wall (3.87% of surface, budget 2%) -- OVER BUDGET; 18 more within measurement error of the limit |
| thickness distribution | PASS | median 1.13 mm, p95 1.27 mm, max 1.60 mm |
| hollowable at 1.20 mm wall | PASS | 0.00 of 0.02 cm3 (0%) in 0 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | spot | 0.13 mm | (-6.8, 2.2, 0.1) | 58 | 1.7 | 1.1 | 1.52 |
| 2 | spot | 0.20 mm | (7.0, 2.1, 0.5) | 45 | 1.3 | 1.1 | 1.15 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
