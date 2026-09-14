# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_deck_0_2.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0004/thickness-deck_0_2.md`

part_deck_0_2.step.py: 156.58 cm3 solid, grid 0.337 mm (479x479x46), 373671 surface samples, thickness resolved to 0.168 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.17) | PASS | 0.0% of surface below (8 of 373671 samples); thinnest 0.34 mm at (120.5, 143.6, 0.8) in 2 region(s); no region is a wall, 1 taper(s) at feature edges and 1 spot(s) too small to be a wall (0.00% of surface, budget 2%); 5 more within measurement error of the limit |
| thickness distribution | PASS | median 6.06 mm, p95 66.71 mm, max 191.54 mm |
| hollowable at 1.20 mm wall | WARN | 77.56 of 156.58 cm3 (50%) in 1 pocket(s) |
| filament that would save | PASS | 11.63 cm3, 14.4 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | spot | 0.34 mm | (123.5, 143.6, 0.3) | 4 | 1.0 | 0.5 | 2.00 |
| 2 | taper | 0.34 mm | (120.5, 143.6, 0.8) | 4 | 1.0 | 3.0 | 0.33 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
