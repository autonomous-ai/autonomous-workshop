# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_white_queen.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/white_queen/r0001/thickness-white_queen.md`

part_white_queen.step.py: 1.66 cm3 solid, grid 0.133 mm (110x110x200), 62634 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (5 of 62634 samples); thinnest 0.13 mm at (-2.5, 4.3, 23.0) in 4 region(s); no region is a wall, 4 taper(s) at feature edges (0.01% of surface, budget 2%); 3 more within measurement error of the limit |
| thickness distribution | PASS | median 7.93 mm, p95 23.93 mm, max 26.00 mm |
| hollowable at 1.20 mm wall | WARN | 0.55 of 1.66 cm3 (33%) in 1 pocket(s), 3 too small to shell |
| filament that would save | PASS | 0.08 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.40 mm | (-1.2, -4.8, 24.1) | 2 | 0.0 | 0.1 | 0.26 |
| 2 | taper | 0.20 mm | (1.2, -2.2, 21.3) | 1 | 0.0 | 0.0 | 0.14 |
| 3 | taper | 0.13 mm | (-2.5, 4.3, 23.0) | 1 | 0.0 | 0.0 | 0.14 |
| 4 | taper | 0.33 mm | (-0.6, -2.4, 24.3) | 1 | 0.0 | 0.0 | 0.14 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
