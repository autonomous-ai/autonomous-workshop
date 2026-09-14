# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/crema_click/part_cup_body.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/crema_click/measure/rounds/r0003/thickness-cup_body.md`

part_cup_body.step.py: 102.41 cm3 solid, grid 0.291 mm (300x225x158), 241045 surface samples, thickness resolved to 0.146 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.15) | FAIL | 0.1% of surface below (204 of 241045 samples); thinnest 0.29 mm at (18.2, 21.4, 0.5) in 9 region(s); 5 wall(s) (widest band 1.22 mm), 3 taper(s) at feature edges and 1 spot(s) too small to be a wall (0.01% of surface, budget 2%); 291 more within measurement error of the limit |
| thickness distribution | PASS | median 20.66 mm, p95 44.39 mm, max 64.47 mm |
| hollowable at 1.20 mm wall | WARN | 76.75 of 102.41 cm3 (75%) in 1 pocket(s) |
| filament that would save | PASS | 11.51 cm3, 14.3 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.29 mm | (18.5, -21.1, 0.4) | 46 | 4.4 | 3.7 | 1.22 |
| 2 | wall | 0.29 mm | (8.4, -26.8, 0.6) | 46 | 4.4 | 5.5 | 0.80 |
| 3 | wall | 0.29 mm | (18.2, 21.4, 0.5) | 44 | 4.2 | 4.6 | 0.90 |
| 4 | wall | 0.44 mm | (9.2, 26.5, 0.4) | 34 | 3.2 | 3.0 | 1.06 |
| 5 | wall | 0.44 mm | (-27.4, 6.0, 0.7) | 17 | 1.6 | 1.7 | 0.93 |
| 6 | taper | 0.44 mm | (-27.0, -5.4, 0.2) | 10 | 1.0 | 1.5 | 0.63 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
