# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_access_receiver_load.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0007/thickness-access_receiver_load.md`

part_access_receiver_load.step.py: 71.99 cm3 solid, grid 0.430 mm (442x339x77), 168048 surface samples, thickness resolved to 0.215 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.22) | FAIL | 0.0% of surface below (46 of 168048 samples); thinnest 0.43 mm at (0.0, 75.6, 3.3) in 4 region(s); 1 wall(s) (widest band 1.82 mm), 3 taper(s) at feature edges (0.02% of surface, budget 2%); 35 more within measurement error of the limit |
| thickness distribution | PASS | median 7.31 mm, p95 30.10 mm, max 159.53 mm |
| hollowable at 1.20 mm wall | WARN | 33.08 of 71.99 cm3 (46%) in 1 pocket(s), 2 too small to shell |
| filament that would save | PASS | 4.96 cm3, 6.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.43 mm | (74.3, 12.9, 6.6) | 14 | 4.4 | 2.4 | 1.82 |
| 2 | taper | 0.43 mm | (0.0, 68.3, 5.0) | 10 | 2.5 | 3.2 | 0.78 |
| 3 | taper | 0.43 mm | (74.8, 131.0, 5.6) | 12 | 2.4 | 3.1 | 0.79 |
| 4 | taper | 0.43 mm | (0.0, 75.6, 3.3) | 10 | 2.1 | 3.3 | 0.65 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
