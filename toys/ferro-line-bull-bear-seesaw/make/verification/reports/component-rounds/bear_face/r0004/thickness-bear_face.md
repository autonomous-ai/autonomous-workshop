# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_bear_face.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/bear_face/r0004/thickness-bear_face.md`

part_bear_face.step.py: 0.72 cm3 solid, grid 0.133 mm (155x120x71), 46408 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 2.3% of surface below (1019 of 46408 samples); thinnest 0.33 mm at (-5.3, 7.3, 1.7) in 2 region(s); 2 wall(s) (widest band 3.23 mm); 108 more within measurement error of the limit |
| thickness distribution | PASS | median 2.00 mm, p95 15.33 mm, max 20.00 mm |
| hollowable at 1.20 mm wall | WARN | 0.06 of 0.72 cm3 (9%) in 1 pocket(s) |
| filament that would save | PASS | 0.01 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.33 mm | (4.7, 7.3, 1.8) | 522 | 10.3 | 3.2 | 3.23 |
| 2 | wall | 0.33 mm | (-5.3, 7.3, 1.7) | 497 | 9.9 | 3.1 | 3.14 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
