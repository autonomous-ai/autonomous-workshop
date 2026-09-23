# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_01_front.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_01_front/r0001/thickness-body_01_front.md`

part_body_01_front.step.py: 3.81 cm3 solid, grid 0.140 mm (415x322x79), 217492 surface samples, thickness resolved to 0.070 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 6.6% of surface below (13471 of 217492 samples); thinnest 0.14 mm at (-21.0, -14.9, 0.0) in 1 region(s); 1 wall(s) (widest band 3.92 mm); 2075 more within measurement error of the limit |
| thickness distribution | PASS | median 1.96 mm, p95 9.94 mm, max 13.16 mm |
| hollowable at 1.20 mm wall | WARN | 0.24 of 3.81 cm3 (6%) in 1 pocket(s) |
| filament that would save | PASS | 0.04 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.14 mm | (-21.0, -14.9, 0.0) | 13471 | 283.3 | 72.2 | 3.92 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
