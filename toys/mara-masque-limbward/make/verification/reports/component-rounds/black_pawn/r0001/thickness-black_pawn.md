# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_black_pawn.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/black_pawn/r0001/thickness-black_pawn.md`

part_black_pawn.step.py: 1.19 cm3 solid, grid 0.133 mm (121x125x95), 41786 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.6% of surface below (259 of 41786 samples); thinnest 0.33 mm at (1.8, 4.0, 11.8) in 1 region(s); no region is a wall, 1 taper(s) at feature edges (0.62% of surface, budget 2%); 11 more within measurement error of the limit |
| thickness distribution | PASS | median 9.07 mm, p95 15.93 mm, max 16.07 mm |
| hollowable at 1.20 mm wall | WARN | 0.44 of 1.19 cm3 (37%) in 1 pocket(s) |
| filament that would save | PASS | 0.07 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.33 mm | (1.8, 4.0, 11.8) | 259 | 4.9 | 9.7 | 0.50 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
