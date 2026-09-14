# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/crema_click/part_cup_body.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/crema_click/measure/rounds/r0005/thickness-cup_body.md`

part_cup_body.step.py: 102.20 cm3 solid, grid 0.291 mm (300x225x158), 240628 surface samples, thickness resolved to 0.146 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.15) | PASS | 0.0% of surface below (8 of 240628 samples); thinnest 0.29 mm at (9.6, 16.8, 4.4) in 2 region(s); no region is a wall, 2 taper(s) at feature edges (0.00% of surface, budget 2%) |
| thickness distribution | PASS | median 20.52 mm, p95 44.39 mm, max 64.47 mm |
| hollowable at 1.20 mm wall | WARN | 76.42 of 102.20 cm3 (75%) in 1 pocket(s) |
| filament that would save | PASS | 11.46 cm3, 14.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.44 mm | (9.5, -16.7, 3.3) | 5 | 0.4 | 1.9 | 0.23 |
| 2 | taper | 0.29 mm | (9.6, 16.8, 4.4) | 3 | 0.3 | 0.4 | 0.56 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
