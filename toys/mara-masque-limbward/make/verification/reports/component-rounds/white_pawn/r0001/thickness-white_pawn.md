# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_white_pawn.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/white_pawn/r0001/thickness-white_pawn.md`

part_white_pawn.step.py: 1.40 cm3 solid, grid 0.133 mm (125x125x95), 44539 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 1.2% of surface below (531 of 44539 samples); thinnest 0.13 mm at (3.5, 4.9, 11.9) in 1 region(s); 1 wall(s) (widest band 0.86 mm); 30 more within measurement error of the limit |
| thickness distribution | PASS | median 9.87 mm, p95 16.00 mm, max 16.07 mm |
| hollowable at 1.20 mm wall | WARN | 0.58 of 1.40 cm3 (42%) in 1 pocket(s) |
| filament that would save | PASS | 0.09 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.13 mm | (3.5, 4.9, 11.9) | 531 | 9.9 | 11.6 | 0.86 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
