# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_07_front.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_07_front/r0002/thickness-body_07_front.md`

part_body_07_front.step.py: 0.64 cm3 solid, grid 0.133 mm (150x141x71), 44673 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 7.0% of surface below (3133 of 44673 samples); thinnest 0.13 mm at (2.7, -1.3, 0.2) in 2 region(s); 1 wall(s) (widest band 4.01 mm), 1 taper(s) at feature edges (0.00% of surface, budget 2%); 942 more within measurement error of the limit |
| thickness distribution | PASS | median 1.20 mm, p95 9.00 mm, max 17.60 mm |
| hollowable at 1.20 mm wall | WARN | 0.14 of 0.64 cm3 (22%) in 1 pocket(s) |
| filament that would save | PASS | 0.02 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.13 mm | (2.7, -1.3, 0.2) | 3132 | 57.2 | 14.2 | 4.01 |
| 2 | taper | 0.73 mm | (-9.6, 1.6, 0.0) | 1 | 0.0 | 0.0 | 0.16 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
