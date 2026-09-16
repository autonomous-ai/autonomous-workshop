# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_circle_twin_tail_comet.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/circle_twin_tail_comet/r0001/thickness-circle_twin_tail_comet.md`

part_circle_twin_tail_comet.step.py: 2.35 cm3 solid, grid 0.133 mm (170x170x215), 87989 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.4% of surface below (155 of 87989 samples); thinnest 0.47 mm at (6.6, 0.5, 28.0) in 9 region(s); no region is a wall, 9 taper(s) at feature edges (0.36% of surface, budget 2%); 230 more within measurement error of the limit |
| thickness distribution | PASS | median 4.20 mm, p95 21.93 mm, max 24.00 mm |
| hollowable at 1.20 mm wall | WARN | 0.73 of 2.35 cm3 (31%) in 1 pocket(s), 6 too small to shell |
| filament that would save | PASS | 0.11 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.73 mm | (-1.6, 5.4, 3.5) | 38 | 1.6 | 2.7 | 0.58 |
| 2 | taper | 0.73 mm | (0.5, -4.6, 3.4) | 34 | 1.5 | 3.0 | 0.51 |
| 3 | taper | 0.73 mm | (-0.9, 9.6, 3.4) | 29 | 1.4 | 2.4 | 0.58 |
| 4 | taper | 0.73 mm | (0.3, -10.4, 3.4) | 39 | 1.1 | 2.6 | 0.43 |
| 5 | taper | 0.60 mm | (1.0, 1.6, 24.0) | 5 | 0.1 | 0.9 | 0.12 |
| 6 | taper | 0.60 mm | (1.0, -1.5, 24.0) | 4 | 0.1 | 0.3 | 0.27 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
