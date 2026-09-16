# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_square_red_giant.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/thickness-square_red_giant.md`

part_square_red_giant.step.py: 5.20 cm3 solid, grid 0.133 mm (170x170x245), 127774 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.2% of surface below (139 of 127774 samples); thinnest 0.73 mm at (0.9, -10.4, 3.4) in 4 region(s); no region is a wall, 4 taper(s) at feature edges (0.21% of surface, budget 2%); 235 more within measurement error of the limit |
| thickness distribution | PASS | median 13.73 mm, p95 26.80 mm, max 32.00 mm |
| hollowable at 1.20 mm wall | WARN | 2.62 of 5.20 cm3 (50%) in 1 pocket(s) |
| filament that would save | PASS | 0.39 cm3, 0.5 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.73 mm | (-0.8, 5.4, 3.6) | 40 | 1.4 | 2.3 | 0.61 |
| 2 | taper | 0.73 mm | (-1.2, 9.6, 3.6) | 42 | 1.4 | 2.4 | 0.56 |
| 3 | taper | 0.73 mm | (0.9, -10.4, 3.4) | 33 | 1.2 | 2.6 | 0.46 |
| 4 | taper | 0.73 mm | (1.0, -4.6, 3.4) | 24 | 1.1 | 2.6 | 0.43 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
