# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_tail_right.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/tail_right/r0001/thickness-tail_right.md`

part_tail_right.step.py: 3.53 cm3 solid, grid 0.133 mm (297x370x38), 143730 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.1% of surface below (96 of 143730 samples); thinnest 0.13 mm at (126.0, 44.8, 0.0) in 10 region(s); no region is a wall, 10 taper(s) at feature edges (0.07% of surface, budget 2%); 34 more within measurement error of the limit |
| thickness distribution | PASS | median 4.00 mm, p95 23.93 mm, max 45.20 mm |
| hollowable at 1.20 mm wall | WARN | 0.96 of 3.53 cm3 (27%) in 2 pocket(s), 4 too small to shell |
| filament that would save | PASS | 0.14 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.27 mm | (123.9, 67.3, 0.3) | 14 | 0.4 | 3.7 | 0.10 |
| 2 | taper | 0.20 mm | (131.8, 51.2, 0.1) | 19 | 0.4 | 4.8 | 0.07 |
| 3 | taper | 0.13 mm | (126.0, 44.8, 0.0) | 15 | 0.2 | 3.1 | 0.08 |
| 4 | taper | 0.27 mm | (130.2, 44.9, 0.1) | 13 | 0.2 | 3.8 | 0.06 |
| 5 | taper | 0.27 mm | (127.2, 53.2, 0.0) | 13 | 0.2 | 1.7 | 0.13 |
| 6 | taper | 0.27 mm | (124.5, 51.5, 0.0) | 9 | 0.2 | 1.8 | 0.09 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
