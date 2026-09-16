# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_piece.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/piece/r0001/thickness-piece.md`

part_piece.step.py: 9.86 cm3 solid, grid 0.140 mm (247x251x190), 186904 surface samples, thickness resolved to 0.070 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 3.3% of surface below (4831 of 186904 samples); thinnest 0.14 mm at (-9.5, -3.7, 17.5) in 18 region(s); 5 wall(s) (widest band 4.78 mm), 12 taper(s) at feature edges and 1 spot(s) too small to be a wall (0.30% of surface, budget 2%); 587 more within measurement error of the limit |
| thickness distribution | PASS | median 20.79 mm, p95 33.95 mm, max 34.51 mm |
| hollowable at 1.20 mm wall | WARN | 5.78 of 9.86 cm3 (59%) in 1 pocket(s) |
| filament that would save | PASS | 0.87 cm3, 1.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.14 mm | (2.7, 10.7, 11.6) | 1932 | 50.5 | 10.6 | 4.78 |
| 2 | wall | 0.14 mm | (-8.3, -7.3, 17.4) | 941 | 23.4 | 14.0 | 1.67 |
| 3 | wall | 0.14 mm | (2.9, -10.6, 15.1) | 816 | 20.9 | 14.0 | 1.49 |
| 4 | wall | 0.14 mm | (3.6, -9.0, 20.4) | 515 | 13.2 | 13.3 | 0.99 |
| 5 | wall | 0.14 mm | (0.9, 8.7, 7.1) | 214 | 5.0 | 6.2 | 0.80 |
| 6 | taper | 0.14 mm | (-8.3, -6.9, 10.6) | 101 | 2.5 | 3.8 | 0.67 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
