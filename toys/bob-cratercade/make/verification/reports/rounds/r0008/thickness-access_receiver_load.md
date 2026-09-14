# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_access_receiver_load.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0008/thickness-access_receiver_load.md`

part_access_receiver_load.step.py: 71.26 cm3 solid, grid 0.430 mm (442x339x77), 166442 surface samples, thickness resolved to 0.215 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.22) | FAIL | 0.0% of surface below (21 of 166442 samples); thinnest 0.43 mm at (0.0, 75.8, 4.8) in 2 region(s); 1 wall(s) (widest band 1.06 mm), 1 taper(s) at feature edges (0.00% of surface, budget 2%); 4 more within measurement error of the limit |
| thickness distribution | PASS | median 7.31 mm, p95 30.53 mm, max 159.53 mm |
| hollowable at 1.20 mm wall | WARN | 32.60 of 71.26 cm3 (46%) in 1 pocket(s), 2 too small to shell |
| filament that would save | PASS | 4.89 cm3, 6.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.43 mm | (0.0, 68.2, 5.8) | 13 | 3.0 | 2.8 | 1.06 |
| 2 | taper | 0.43 mm | (0.0, 75.8, 4.8) | 8 | 1.7 | 2.9 | 0.59 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
