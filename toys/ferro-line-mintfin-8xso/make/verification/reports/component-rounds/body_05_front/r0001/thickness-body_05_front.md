# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_05_front.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_05_front/r0001/thickness-body_05_front.md`

part_body_05_front.step.py: 3.06 cm3 solid, grid 0.133 mm (276x241x82), 123123 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 2.3% of surface below (2640 of 123123 samples); thinnest 0.13 mm at (-0.4, 15.1, 2.0) in 3 region(s); 2 wall(s) (widest band 2.92 mm), 1 taper(s) at feature edges (0.00% of surface, budget 2%); 62 more within measurement error of the limit |
| thickness distribution | PASS | median 3.47 mm, p95 29.40 mm, max 36.20 mm |
| hollowable at 1.20 mm wall | WARN | 0.78 of 3.06 cm3 (26%) in 1 pocket(s) |
| filament that would save | PASS | 0.12 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.13 mm | (4.2, -11.6, 3.4) | 2275 | 44.2 | 15.1 | 2.92 |
| 2 | wall | 0.13 mm | (-0.4, 15.1, 2.0) | 364 | 6.8 | 5.0 | 1.36 |
| 3 | taper | 0.73 mm | (2.0, 15.5, 0.0) | 1 | 0.0 | 0.0 | 0.20 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
