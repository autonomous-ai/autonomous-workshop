# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_frame.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/frame/r0001/thickness-frame.md`

part_frame.step.py: 6.23 cm3 solid, grid 0.228 mm (292x292x130), 163887 surface samples, thickness resolved to 0.114 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.11) | FAIL | 0.4% of surface below (679 of 163887 samples); thinnest 0.23 mm at (9.4, 7.8, 3.7) in 44 region(s); 5 wall(s) (widest band 2.75 mm), 36 taper(s) at feature edges and 3 spot(s) too small to be a wall (0.09% of surface, budget 2%); 59 more within measurement error of the limit |
| thickness distribution | PASS | median 1.94 mm, p95 8.44 mm, max 32.38 mm |
| hollowable at 1.20 mm wall | WARN | 0.01 of 6.23 cm3 (0%) in 1 pocket(s), 3 too small to shell |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.23 mm | (-18.2, -13.7, 1.0) | 168 | 10.3 | 3.7 | 2.75 |
| 2 | wall | 0.23 mm | (21.2, -8.2, 1.0) | 139 | 8.7 | 3.5 | 2.47 |
| 3 | wall | 0.23 mm | (-2.5, 22.6, 1.8) | 137 | 8.7 | 3.3 | 2.65 |
| 4 | wall | 0.23 mm | (-9.0, 21.2, 0.3) | 54 | 4.0 | 2.3 | 1.78 |
| 5 | wall | 0.23 mm | (9.0, -21.2, 0.8) | 51 | 3.9 | 2.3 | 1.71 |
| 6 | taper | 0.68 mm | (26.3, 0.3, 13.5) | 18 | 1.2 | 1.9 | 0.62 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
