# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_northeast_panel.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/thickness-northeast_panel.md`

part_northeast_panel.step.py: 97.09 cm3 solid, grid 0.217 mm (585x723x28), 370508 surface samples, thickness resolved to 0.109 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.11) | PASS | 0.0% of surface below (9 of 370508 samples); thinnest 0.33 mm at (13.5, 150.4, 4.6) in 2 region(s); no region is a wall, 0 taper(s) at feature edges and 2 spot(s) too small to be a wall (0.01% of surface, budget 2%); 526 more within measurement error of the limit |
| thickness distribution | PASS | median 5.00 mm, p95 125.86 mm, max 155.94 mm |
| hollowable at 1.20 mm wall | WARN | 43.16 of 97.09 cm3 (44%) in 1 pocket(s) |
| filament that would save | PASS | 6.47 cm3, 8.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | spot | 0.33 mm | (16.5, 150.4, 4.7) | 5 | 1.9 | 1.1 | 1.82 |
| 2 | spot | 0.33 mm | (13.5, 150.4, 4.6) | 4 | 1.9 | 0.9 | 2.06 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
