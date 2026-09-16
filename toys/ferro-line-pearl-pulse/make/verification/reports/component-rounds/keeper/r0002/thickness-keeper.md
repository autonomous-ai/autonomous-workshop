# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_keeper.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/keeper/r0002/thickness-keeper.md`

part_keeper.step.py: 0.72 cm3 solid, grid 0.133 mm (382x382x14), 81591 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 0.9% of surface below (649 of 81591 samples); thinnest 0.13 mm at (-1.3, -25.2, 0.7) in 12 region(s); 3 wall(s) (widest band 1.45 mm), 9 taper(s) at feature edges (0.08% of surface, budget 2%); 131 more within measurement error of the limit |
| thickness distribution | PASS | median 1.20 mm, p95 5.00 mm, max 27.87 mm |
| hollowable at 1.20 mm wall | PASS | 0.00 of 0.72 cm3 (0%) in 0 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.53 mm | (21.1, 10.9, 0.1) | 236 | 4.7 | 3.4 | 1.38 |
| 2 | wall | 0.53 mm | (-19.8, 12.8, 0.2) | 226 | 4.7 | 3.3 | 1.43 |
| 3 | wall | 0.13 mm | (-1.3, -25.2, 0.7) | 136 | 3.2 | 2.2 | 1.45 |
| 4 | taper | 0.13 mm | (-18.1, 15.1, 0.0) | 34 | 0.9 | 1.1 | 0.78 |
| 5 | taper | 0.60 mm | (19.3, -16.2, 1.0) | 3 | 0.1 | 0.6 | 0.15 |
| 6 | taper | 0.53 mm | (7.3, 24.0, 0.4) | 3 | 0.1 | 0.2 | 0.33 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
