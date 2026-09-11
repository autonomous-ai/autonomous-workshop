# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/crema_click/part_cup_body.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/crema_click/measure/rounds/r0002/thickness-cup_body.md`

part_cup_body.step.py: 103.09 cm3 solid, grid 0.291 mm (300x225x158), 241319 surface samples, thickness resolved to 0.146 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.15) | FAIL | 0.1% of surface below (236 of 241319 samples); thinnest 0.29 mm at (11.1, -19.9, 0.0) in 4 region(s); 3 wall(s) (widest band 1.05 mm), 1 taper(s) at feature edges (0.00% of surface, budget 2%); 38 more within measurement error of the limit |
| thickness distribution | PASS | median 20.66 mm, p95 44.39 mm, max 64.47 mm |
| hollowable at 1.20 mm wall | WARN | 77.23 of 103.09 cm3 (75%) in 1 pocket(s), 6 too small to shell |
| filament that would save | PASS | 11.58 cm3, 14.4 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.29 mm | (-22.8, -4.2, 0.0) | 97 | 9.5 | 9.8 | 0.97 |
| 2 | wall | 0.29 mm | (12.8, 18.7, 0.0) | 76 | 7.5 | 7.2 | 1.05 |
| 3 | wall | 0.29 mm | (11.1, -19.9, 0.0) | 58 | 5.6 | 6.6 | 0.85 |
| 4 | taper | 0.58 mm | (9.9, 17.1, 2.3) | 5 | 0.4 | 1.1 | 0.37 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
