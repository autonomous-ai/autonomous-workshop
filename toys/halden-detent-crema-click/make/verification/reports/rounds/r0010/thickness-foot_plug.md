# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/crema_click/part_foot_plug.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/crema_click/measure/rounds/r0010/thickness-foot_plug.md`

part_foot_plug.step.py: 13.88 cm3 solid, grid 0.147 mm (385x386x77), 289366 surface samples, thickness resolved to 0.074 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 0.5% of surface below (1331 of 289366 samples); thinnest 0.15 mm at (-14.0, -20.6, 10.5) in 4 region(s); 3 wall(s) (widest band 1.13 mm), 1 taper(s) at feature edges (0.00% of surface, budget 2%); 84 more within measurement error of the limit |
| thickness distribution | PASS | median 5.44 mm, p95 55.93 mm, max 56.01 mm |
| hollowable at 1.20 mm wall | WARN | 6.95 of 13.88 cm3 (50%) in 4 pocket(s) |
| filament that would save | PASS | 1.04 cm3, 1.3 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.15 mm | (24.9, 3.3, 10.5) | 461 | 11.0 | 9.7 | 1.13 |
| 2 | wall | 0.15 mm | (-14.0, -20.6, 10.5) | 447 | 10.8 | 9.9 | 1.09 |
| 3 | wall | 0.15 mm | (-10.5, 22.7, 10.5) | 422 | 10.2 | 9.9 | 1.02 |
| 4 | taper | 0.44 mm | (-15.7, 17.2, 8.0) | 1 | 0.0 | 0.0 | 0.16 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
