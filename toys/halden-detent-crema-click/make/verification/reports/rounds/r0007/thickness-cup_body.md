# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/crema_click/part_cup_body.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/crema_click/measure/rounds/r0007/thickness-cup_body.md`

part_cup_body.step.py: 100.64 cm3 solid, grid 0.291 mm (300x225x158), 241773 surface samples, thickness resolved to 0.146 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.15) | PASS | 0.0% of surface below (5 of 241773 samples); thinnest 0.29 mm at (9.6, -16.8, 4.2) in 2 region(s); no region is a wall, 2 taper(s) at feature edges (0.00% of surface, budget 2%); 4 more within measurement error of the limit |
| thickness distribution | PASS | median 20.37 mm, p95 44.39 mm, max 44.53 mm |
| hollowable at 1.20 mm wall | WARN | 74.88 of 100.64 cm3 (74%) in 2 pocket(s) |
| filament that would save | PASS | 11.23 cm3, 13.9 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.29 mm | (9.6, -16.8, 4.2) | 4 | 0.3 | 0.5 | 0.72 |
| 2 | taper | 0.29 mm | (9.5, 16.7, 4.3) | 1 | 0.1 | 0.0 | 0.29 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
