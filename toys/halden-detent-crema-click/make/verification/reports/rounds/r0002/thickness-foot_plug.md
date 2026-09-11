# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/crema_click/part_foot_plug.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/crema_click/measure/rounds/r0002/thickness-foot_plug.md`

part_foot_plug.step.py: 13.98 cm3 solid, grid 0.140 mm (404x405x73), 319800 surface samples, thickness resolved to 0.070 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 0.5% of surface below (1611 of 319800 samples); thinnest 0.14 mm at (-17.0, -19.9, 9.4) in 3 region(s); 3 wall(s) (widest band 1.17 mm); 75 more within measurement error of the limit |
| thickness distribution | PASS | median 5.46 mm, p95 55.93 mm, max 56.00 mm |
| hollowable at 1.20 mm wall | WARN | 6.68 of 13.98 cm3 (48%) in 4 pocket(s) |
| filament that would save | PASS | 1.00 cm3, 1.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.14 mm | (-15.5, 20.7, 9.4) | 543 | 11.5 | 10.0 | 1.15 |
| 2 | wall | 0.14 mm | (-17.0, -19.9, 9.4) | 537 | 11.4 | 10.0 | 1.14 |
| 3 | wall | 0.14 mm | (25.7, -4.7, 9.4) | 531 | 11.3 | 9.7 | 1.17 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
