# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_01_front.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_01_front/r0002/thickness-body_01_front.md`

part_body_01_front.step.py: 5.81 cm3 solid, grid 0.140 mm (415x322x79), 225178 surface samples, thickness resolved to 0.070 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 3.4% of surface below (7510 of 225178 samples); thinnest 0.14 mm at (-1.7, 22.1, 1.0) in 9 region(s); 2 wall(s) (widest band 4.93 mm), 7 taper(s) at feature edges (0.17% of surface, budget 2%); 120 more within measurement error of the limit |
| thickness distribution | PASS | median 3.15 mm, p95 11.83 mm, max 57.47 mm |
| hollowable at 1.20 mm wall | WARN | 1.08 of 5.81 cm3 (19%) in 1 pocket(s) |
| filament that would save | PASS | 0.16 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.14 mm | (12.3, -14.4, 3.1) | 6874 | 141.6 | 28.7 | 4.93 |
| 2 | wall | 0.14 mm | (-1.7, 22.1, 1.0) | 313 | 6.7 | 4.2 | 1.58 |
| 3 | taper | 0.14 mm | (20.1, -11.1, 2.6) | 168 | 4.0 | 7.1 | 0.56 |
| 4 | taper | 0.14 mm | (-20.1, -11.1, 2.7) | 147 | 3.7 | 6.8 | 0.54 |
| 5 | taper | 0.49 mm | (-16.1, -14.8, 2.5) | 3 | 0.1 | 0.3 | 0.27 |
| 6 | taper | 0.14 mm | (-18.6, -15.3, 2.1) | 2 | 0.0 | 0.3 | 0.18 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
