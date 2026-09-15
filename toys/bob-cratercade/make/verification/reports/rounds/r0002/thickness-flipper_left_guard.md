# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_flipper_left_guard.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0002/thickness-flipper_left_guard.md`

part_flipper_left_guard.step.py: 15.87 cm3 solid, grid 0.251 mm (472x257x92), 198435 surface samples, thickness resolved to 0.126 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.13) | FAIL | 0.2% of surface below (427 of 198435 samples); thinnest 0.25 mm at (-64.8, 46.0, 0.8) in 13 region(s); 4 wall(s) (widest band 4.11 mm), 9 taper(s) at feature edges (0.02% of surface, budget 2%); 215 more within measurement error of the limit |
| thickness distribution | PASS | median 2.89 mm, p95 24.01 mm, max 114.90 mm |
| hollowable at 1.20 mm wall | WARN | 1.82 of 15.87 cm3 (11%) in 1 pocket(s), 11 too small to shell |
| filament that would save | PASS | 0.27 cm3, 0.3 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.38 mm | (-60.2, 8.0, 0.4) | 274 | 19.3 | 4.7 | 4.11 |
| 2 | wall | 0.25 mm | (46.8, 28.7, 2.6) | 43 | 3.4 | 2.8 | 1.22 |
| 3 | wall | 0.25 mm | (47.0, 23.1, 2.0) | 43 | 3.1 | 2.7 | 1.15 |
| 4 | wall | 0.25 mm | (-64.8, 46.0, 0.8) | 36 | 2.8 | 2.5 | 1.15 |
| 5 | taper | 0.25 mm | (-57.2, 45.7, 0.7) | 19 | 1.3 | 2.3 | 0.57 |
| 6 | taper | 0.50 mm | (45.1, 27.3, 22.0) | 2 | 0.1 | 0.1 | 0.58 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
