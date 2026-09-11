# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/crema_click/part_cup_body.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/crema_click/measure/rounds/r0001/thickness-cup_body.md`

part_cup_body.step.py: 103.15 cm3 solid, grid 0.291 mm (300x225x158), 240925 surface samples, thickness resolved to 0.146 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.15) | FAIL | 0.0% of surface below (44 of 240925 samples); thinnest 0.29 mm at (-11.5, -18.1, 0.5) in 2 region(s); 1 wall(s) (widest band 0.80 mm), 1 taper(s) at feature edges (0.01% of surface, budget 2%); 23 more within measurement error of the limit |
| thickness distribution | PASS | median 20.66 mm, p95 44.39 mm, max 64.47 mm |
| hollowable at 1.20 mm wall | WARN | 77.29 of 103.15 cm3 (75%) in 1 pocket(s) |
| filament that would save | PASS | 11.59 cm3, 14.4 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.29 mm | (-11.5, 18.4, 1.2) | 23 | 3.0 | 3.7 | 0.80 |
| 2 | taper | 0.29 mm | (-11.5, -18.1, 0.5) | 21 | 2.9 | 3.7 | 0.79 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
