# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_04_front.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_04_front/r0001/thickness-body_04_front.md`

part_body_04_front.step.py: 4.44 cm3 solid, grid 0.133 mm (356x301x81), 187889 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 2.5% of surface below (4546 of 187889 samples); thinnest 0.13 mm at (0.4, 18.8, 2.1) in 5 region(s); 2 wall(s) (widest band 3.62 mm), 3 taper(s) at feature edges (0.01% of surface, budget 2%); 14 more within measurement error of the limit |
| thickness distribution | PASS | median 3.13 mm, p95 12.40 mm, max 46.87 mm |
| hollowable at 1.20 mm wall | WARN | 0.92 of 4.44 cm3 (21%) in 1 pocket(s) |
| filament that would save | PASS | 0.14 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.13 mm | (3.9, -14.8, 3.2) | 4135 | 78.1 | 21.6 | 3.62 |
| 2 | wall | 0.13 mm | (0.4, 18.8, 2.1) | 403 | 7.6 | 4.8 | 1.60 |
| 3 | taper | 0.40 mm | (-13.2, -13.7, 2.6) | 5 | 0.1 | 0.3 | 0.42 |
| 4 | taper | 0.47 mm | (13.3, -13.8, 2.4) | 2 | 0.0 | 0.1 | 0.31 |
| 5 | taper | 0.47 mm | (7.6, -18.7, 0.0) | 1 | 0.0 | 0.0 | 0.18 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
