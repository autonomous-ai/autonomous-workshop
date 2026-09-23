# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_tear_back.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/tear_back/r0007/thickness-tear_back.md`

part_tear_back.step.py: 24.80 cm3 solid, grid 0.154 mm (453x378x67), 339109 surface samples, thickness resolved to 0.077 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.08) | FAIL | 0.6% of surface below (1863 of 339109 samples); thinnest 0.15 mm at (-20.4, 26.9, 0.7) in 8 region(s); 8 wall(s) (widest band 2.47 mm); 320 more within measurement error of the limit |
| thickness distribution | PASS | median 9.57 mm, p95 69.07 mm, max 69.15 mm |
| hollowable at 1.20 mm wall | WARN | 15.92 of 24.80 cm3 (64%) in 1 pocket(s) |
| filament that would save | PASS | 2.39 cm3, 3.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.15 mm | (-29.6, 17.9, 0.7) | 311 | 8.2 | 3.3 | 2.47 |
| 2 | wall | 0.15 mm | (20.5, 27.0, 2.1) | 293 | 7.9 | 3.2 | 2.45 |
| 3 | wall | 0.15 mm | (-29.5, 27.0, 0.5) | 283 | 7.6 | 3.2 | 2.38 |
| 4 | wall | 0.15 mm | (29.6, 17.9, 0.3) | 280 | 7.5 | 3.3 | 2.27 |
| 5 | wall | 0.15 mm | (-20.4, 26.9, 0.7) | 269 | 7.3 | 3.2 | 2.25 |
| 6 | wall | 0.15 mm | (29.5, 26.9, 1.6) | 245 | 6.7 | 3.2 | 2.10 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
