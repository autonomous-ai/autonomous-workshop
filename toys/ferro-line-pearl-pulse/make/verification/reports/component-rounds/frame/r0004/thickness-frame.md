# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_frame.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/frame/r0004/thickness-frame.md`

part_frame.step.py: 7.41 cm3 solid, grid 0.228 mm (292x292x128), 191304 surface samples, thickness resolved to 0.114 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.11) | FAIL | 0.2% of surface below (258 of 191304 samples); thinnest 0.23 mm at (24.5, 19.4, 13.5) in 31 region(s); 4 wall(s) (widest band 2.31 mm), 26 taper(s) at feature edges and 1 spot(s) too small to be a wall (0.07% of surface, budget 2%); 23 more within measurement error of the limit |
| thickness distribution | PASS | median 1.94 mm, p95 8.78 mm, max 36.72 mm |
| hollowable at 1.20 mm wall | WARN | 0.01 of 7.41 cm3 (0%) in 1 pocket(s), 3 too small to shell |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.23 mm | (-3.2, 27.9, 14.9) | 40 | 3.8 | 1.7 | 2.23 |
| 2 | wall | 0.23 mm | (-2.9, 27.6, 12.3) | 43 | 3.7 | 1.6 | 2.31 |
| 3 | wall | 0.23 mm | (-22.0, -17.0, 12.4) | 43 | 3.3 | 2.0 | 1.65 |
| 4 | wall | 0.23 mm | (-21.8, -17.2, 14.8) | 34 | 2.7 | 1.8 | 1.53 |
| 5 | taper | 0.68 mm | (-18.4, 22.6, 17.2) | 8 | 0.6 | 1.2 | 0.48 |
| 6 | taper | 0.68 mm | (18.5, -22.6, 17.2) | 7 | 0.6 | 1.1 | 0.49 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
