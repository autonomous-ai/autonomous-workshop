# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/crema_click/part_cup_body.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/crema_click/measure/rounds/r0008/thickness-cup_body.md`

part_cup_body.step.py: 100.88 cm3 solid, grid 0.291 mm (300x225x158), 242839 surface samples, thickness resolved to 0.146 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.15) | PASS | 0.0% of surface below (10 of 242839 samples); thinnest 0.29 mm at (9.6, 16.8, 4.7) in 3 region(s); no region is a wall, 2 taper(s) at feature edges and 1 spot(s) too small to be a wall (0.01% of surface, budget 2%) |
| thickness distribution | PASS | median 20.37 mm, p95 44.39 mm, max 44.53 mm |
| hollowable at 1.20 mm wall | WARN | 75.03 of 100.88 cm3 (74%) in 2 pocket(s) |
| filament that would save | PASS | 11.25 cm3, 14.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.44 mm | (9.6, -16.8, 4.2) | 6 | 0.5 | 2.2 | 0.23 |
| 2 | spot | 0.44 mm | (-16.6, -16.8, 0.4) | 1 | 0.4 | 0.0 | 1.20 |
| 3 | taper | 0.29 mm | (9.6, 16.8, 4.7) | 3 | 0.3 | 1.2 | 0.21 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
