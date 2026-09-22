# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_03_front.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_03_front/r0003/thickness-body_03_front.md`

part_body_03_front.step.py: 5.08 cm3 solid, grid 0.133 mm (403x310x83), 211051 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 0.7% of surface below (1475 of 211051 samples); thinnest 0.13 mm at (4.9, 12.5, 1.2) in 8 region(s); 1 wall(s) (widest band 2.69 mm), 7 taper(s) at feature edges (0.03% of surface, budget 2%); 287 more within measurement error of the limit |
| thickness distribution | PASS | median 3.13 mm, p95 13.87 mm, max 53.07 mm |
| hollowable at 1.20 mm wall | WARN | 1.00 of 5.08 cm3 (20%) in 1 pocket(s) |
| filament that would save | PASS | 0.15 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.13 mm | (4.9, 12.5, 1.2) | 1445 | 27.7 | 10.3 | 2.69 |
| 2 | taper | 0.27 mm | (-0.4, 16.1, 3.2) | 16 | 0.6 | 2.5 | 0.25 |
| 3 | taper | 0.20 mm | (1.7, 15.8, 3.2) | 5 | 0.2 | 1.4 | 0.11 |
| 4 | taper | 0.33 mm | (-3.8, 13.7, 1.3) | 2 | 0.1 | 0.0 | 0.48 |
| 5 | taper | 0.27 mm | (-7.0, 6.6, 3.2) | 4 | 0.1 | 1.0 | 0.06 |
| 6 | taper | 0.27 mm | (4.2, 14.2, 2.3) | 1 | 0.1 | 0.0 | 0.46 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
