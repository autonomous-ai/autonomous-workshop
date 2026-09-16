# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_frame.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/frame/r0003/thickness-frame.md`

part_frame.step.py: 7.43 cm3 solid, grid 0.228 mm (292x292x128), 192092 surface samples, thickness resolved to 0.114 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.11) | FAIL | 0.3% of surface below (478 of 192092 samples); thinnest 0.23 mm at (-24.5, 19.4, 13.6) in 33 region(s); 2 wall(s) (widest band 1.14 mm), 30 taper(s) at feature edges and 1 spot(s) too small to be a wall (0.18% of surface, budget 2%); 130 more within measurement error of the limit |
| thickness distribution | PASS | median 1.94 mm, p95 8.78 mm, max 36.72 mm |
| hollowable at 1.20 mm wall | WARN | 0.01 of 7.43 cm3 (0%) in 1 pocket(s), 3 too small to shell |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.23 mm | (-20.6, -17.8, 3.4) | 151 | 8.1 | 11.3 | 0.72 |
| 2 | taper | 0.23 mm | (-3.2, 27.4, 12.7) | 100 | 5.3 | 10.7 | 0.49 |
| 3 | wall | 0.23 mm | (-20.6, -17.8, 15.0) | 84 | 4.9 | 4.3 | 1.14 |
| 4 | wall | 0.23 mm | (-2.1, 27.0, 14.2) | 58 | 3.4 | 3.2 | 1.09 |
| 5 | taper | 0.68 mm | (-22.3, 18.7, 17.2) | 9 | 0.7 | 0.9 | 0.80 |
| 6 | taper | 0.23 mm | (17.9, 23.0, 16.5) | 6 | 0.5 | 1.2 | 0.41 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
