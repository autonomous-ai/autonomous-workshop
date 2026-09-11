# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/crema_click/part_cup_body.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/crema_click/measure/rounds/r0004/thickness-cup_body.md`

part_cup_body.step.py: 101.80 cm3 solid, grid 0.291 mm (300x225x158), 237614 surface samples, thickness resolved to 0.146 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.15) | FAIL | 0.3% of surface below (472 of 237614 samples); thinnest 0.29 mm at (18.1, 21.0, 1.5) in 4 region(s); 3 wall(s) (widest band 1.61 mm), 1 taper(s) at feature edges (0.00% of surface, budget 2%); 372 more within measurement error of the limit |
| thickness distribution | PASS | median 20.52 mm, p95 41.77 mm, max 64.47 mm |
| hollowable at 1.20 mm wall | WARN | 76.37 of 101.80 cm3 (75%) in 1 pocket(s) |
| filament that would save | PASS | 11.46 cm3, 14.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.29 mm | (8.8, -26.4, 1.6) | 181 | 21.4 | 13.6 | 1.57 |
| 2 | wall | 0.29 mm | (18.1, 21.0, 1.5) | 171 | 21.1 | 13.0 | 1.61 |
| 3 | wall | 0.29 mm | (-27.2, 5.8, 1.6) | 117 | 15.3 | 12.2 | 1.26 |
| 4 | taper | 0.58 mm | (9.3, -16.4, 3.3) | 3 | 0.3 | 0.6 | 0.43 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
