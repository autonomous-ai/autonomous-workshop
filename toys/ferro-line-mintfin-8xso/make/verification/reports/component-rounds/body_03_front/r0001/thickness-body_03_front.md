# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_03_front.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_03_front/r0001/thickness-body_03_front.md`

part_body_03_front.step.py: 5.24 cm3 solid, grid 0.133 mm (403x319x83), 224262 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 3.0% of surface below (6646 of 224262 samples); thinnest 0.13 mm at (0.4, 19.7, 2.0) in 10 region(s); 2 wall(s) (widest band 4.28 mm), 8 taper(s) at feature edges (0.01% of surface, budget 2%); 32 more within measurement error of the limit |
| thickness distribution | PASS | median 3.13 mm, p95 11.07 mm, max 53.07 mm |
| hollowable at 1.20 mm wall | WARN | 1.06 of 5.24 cm3 (20%) in 1 pocket(s) |
| filament that would save | PASS | 0.16 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.13 mm | (9.8, -14.1, 3.2) | 6221 | 115.8 | 27.0 | 4.28 |
| 2 | wall | 0.13 mm | (0.4, 19.7, 2.0) | 409 | 7.6 | 4.8 | 1.59 |
| 3 | taper | 0.47 mm | (-14.5, -14.1, 2.5) | 5 | 0.1 | 0.5 | 0.25 |
| 4 | taper | 0.33 mm | (15.5, -14.2, 2.5) | 3 | 0.1 | 0.2 | 0.29 |
| 5 | taper | 0.27 mm | (-15.6, -14.3, 2.5) | 2 | 0.1 | 0.2 | 0.37 |
| 6 | taper | 0.73 mm | (13.9, -14.0, 2.6) | 2 | 0.0 | 0.9 | 0.05 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
