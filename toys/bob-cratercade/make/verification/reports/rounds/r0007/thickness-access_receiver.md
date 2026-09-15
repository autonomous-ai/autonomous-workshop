# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_access_receiver.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0007/thickness-access_receiver.md`

part_access_receiver.step.py: 72.09 cm3 solid, grid 0.430 mm (442x339x77), 167900 surface samples, thickness resolved to 0.215 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.22) | FAIL | 0.0% of surface below (44 of 167900 samples); thinnest 0.43 mm at (187.5, 68.3, 6.3) in 4 region(s); 2 wall(s) (widest band 1.50 mm), 1 taper(s) at feature edges and 1 spot(s) too small to be a wall (0.00% of surface, budget 2%); 40 more within measurement error of the limit |
| thickness distribution | PASS | median 7.31 mm, p95 30.10 mm, max 159.96 mm |
| hollowable at 1.20 mm wall | WARN | 33.12 of 72.09 cm3 (46%) in 1 pocket(s) |
| filament that would save | PASS | 4.97 cm3, 6.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.43 mm | (113.6, 12.9, 6.5) | 20 | 5.2 | 3.5 | 1.50 |
| 2 | wall | 0.43 mm | (113.1, 131.0, 5.6) | 16 | 3.6 | 3.6 | 0.99 |
| 3 | taper | 0.43 mm | (187.5, 68.3, 6.3) | 4 | 1.0 | 1.5 | 0.66 |
| 4 | spot | 0.43 mm | (187.7, 75.3, 6.5) | 4 | 0.7 | 0.7 | 1.04 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
