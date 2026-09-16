# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_shaft.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/shaft/r0002/thickness-shaft.md`

part_shaft.step.py: 0.28 cm3 solid, grid 0.133 mm (71x203x29), 22098 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 3.4% of surface below (751 of 22098 samples); thinnest 0.13 mm at (0.8, -106.9, 0.4) in 4 region(s); 4 wall(s) (widest band 1.54 mm); 65 more within measurement error of the limit |
| thickness distribution | PASS | median 3.13 mm, p95 8.73 mm, max 22.00 mm |
| hollowable at 1.20 mm wall | WARN | 0.01 of 0.28 cm3 (3%) in 1 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.13 mm | (-0.7, -108.0, 0.3) | 197 | 4.3 | 2.8 | 1.54 |
| 2 | wall | 0.13 mm | (-0.6, -106.1, 2.8) | 186 | 4.0 | 2.7 | 1.49 |
| 3 | wall | 0.13 mm | (0.7, -108.2, 2.9) | 188 | 3.9 | 2.8 | 1.43 |
| 4 | wall | 0.13 mm | (0.8, -106.9, 0.4) | 180 | 3.9 | 2.8 | 1.42 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
