# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_square_twin_tail_comet.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/square_twin_tail_comet/r0001/thickness-square_twin_tail_comet.md`

part_square_twin_tail_comet.step.py: 2.62 cm3 solid, grid 0.133 mm (170x170x215), 98722 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.3% of surface below (174 of 98722 samples); thinnest 0.60 mm at (6.6, -1.1, 28.0) in 7 region(s); no region is a wall, 7 taper(s) at feature edges (0.33% of surface, budget 2%); 234 more within measurement error of the limit |
| thickness distribution | PASS | median 3.60 mm, p95 22.00 mm, max 26.93 mm |
| hollowable at 1.20 mm wall | WARN | 0.79 of 2.62 cm3 (30%) in 1 pocket(s), 7 too small to shell |
| filament that would save | PASS | 0.12 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.73 mm | (-0.7, 5.4, 3.3) | 42 | 1.6 | 2.9 | 0.55 |
| 2 | taper | 0.73 mm | (0.8, -4.6, 3.4) | 34 | 1.6 | 3.0 | 0.52 |
| 3 | taper | 0.73 mm | (-0.4, 9.6, 3.4) | 39 | 1.4 | 2.4 | 0.57 |
| 4 | taper | 0.73 mm | (1.2, -10.4, 3.6) | 35 | 1.1 | 2.6 | 0.43 |
| 5 | taper | 0.60 mm | (6.6, -1.1, 28.0) | 13 | 0.3 | 3.4 | 0.08 |
| 6 | taper | 0.73 mm | (0.9, 1.4, 24.0) | 9 | 0.2 | 1.9 | 0.10 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
