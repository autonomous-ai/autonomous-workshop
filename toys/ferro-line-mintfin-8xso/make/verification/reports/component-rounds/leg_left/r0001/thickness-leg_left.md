# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_leg_left.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/leg_left/r0001/thickness-leg_left.md`

part_leg_left.step.py: 5.45 cm3 solid, grid 0.133 mm (211x200x147), 110897 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 1.3% of surface below (1333 of 110897 samples); thinnest 0.13 mm at (8.3, -8.2, 0.8) in 5 region(s); 3 wall(s) (widest band 1.92 mm), 2 taper(s) at feature edges (0.04% of surface, budget 2%); 126 more within measurement error of the limit |
| thickness distribution | PASS | median 13.20 mm, p95 23.87 mm, max 27.60 mm |
| hollowable at 1.20 mm wall | WARN | 3.30 of 5.45 cm3 (61%) in 1 pocket(s), 6 too small to shell |
| filament that would save | PASS | 0.50 cm3, 0.6 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.13 mm | (8.3, -8.2, 0.8) | 717 | 13.3 | 7.6 | 1.75 |
| 2 | wall | 0.13 mm | (0.3, -13.8, 1.7) | 409 | 8.3 | 4.3 | 1.92 |
| 3 | wall | 0.53 mm | (-6.7, -13.0, 0.3) | 172 | 3.6 | 2.5 | 1.43 |
| 4 | taper | 0.13 mm | (12.0, 9.3, 19.0) | 26 | 0.5 | 2.7 | 0.17 |
| 5 | taper | 0.13 mm | (9.9, 11.1, 19.0) | 9 | 0.2 | 1.9 | 0.13 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
