# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_board.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/board/r0002/thickness-board.md`

part_board.step.py: 321.54 cm3 solid, grid 0.371 mm (532x532x37), 360091 surface samples, thickness resolved to 0.186 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.19) | PASS | 0.0% of surface below (104 of 360091 samples); thinnest 0.37 mm at (54.2, -36.4, 11.3) in 36 region(s); no region is a wall, 36 taper(s) at feature edges (0.01% of surface, budget 2%); 343 more within measurement error of the limit |
| thickness distribution | PASS | median 11.89 mm, p95 151.93 mm, max 203.19 mm |
| hollowable at 1.20 mm wall | WARN | 237.84 of 321.54 cm3 (74%) in 1 pocket(s) |
| filament that would save | PASS | 35.68 cm3, 44.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.56 mm | (54.2, -0.4, 10.4) | 5 | 0.5 | 1.7 | 0.29 |
| 2 | taper | 0.56 mm | (-54.4, 17.8, 11.4) | 5 | 0.5 | 1.5 | 0.34 |
| 3 | taper | 0.56 mm | (-18.2, 53.6, 11.5) | 5 | 0.5 | 1.5 | 0.33 |
| 4 | taper | 0.56 mm | (-36.3, 54.2, 11.5) | 4 | 0.4 | 1.3 | 0.30 |
| 5 | taper | 0.56 mm | (35.8, -17.6, 11.3) | 4 | 0.4 | 0.9 | 0.42 |
| 6 | taper | 0.56 mm | (-0.2, -17.6, 11.3) | 4 | 0.4 | 1.5 | 0.27 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
