# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_04_front.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_04_front/r0003/thickness-body_04_front.md`

part_body_04_front.step.py: 4.33 cm3 solid, grid 0.133 mm (356x293x81), 182576 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 1.1% of surface below (1807 of 182576 samples); thinnest 0.13 mm at (-2.7, 12.5, 0.0) in 6 region(s); 1 wall(s) (widest band 3.24 mm), 5 taper(s) at feature edges (0.03% of surface, budget 2%); 347 more within measurement error of the limit |
| thickness distribution | PASS | median 3.13 mm, p95 11.87 mm, max 46.87 mm |
| hollowable at 1.20 mm wall | WARN | 0.83 of 4.33 cm3 (19%) in 1 pocket(s) |
| filament that would save | PASS | 0.12 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.13 mm | (-2.7, 12.5, 0.0) | 1761 | 34.9 | 10.8 | 3.24 |
| 2 | taper | 0.13 mm | (1.6, 15.0, 3.1) | 37 | 0.9 | 5.4 | 0.17 |
| 3 | taper | 0.20 mm | (-7.1, 5.9, 3.2) | 4 | 0.1 | 0.7 | 0.08 |
| 4 | taper | 0.20 mm | (6.7, 4.9, 3.2) | 2 | 0.0 | 0.0 | 0.22 |
| 5 | taper | 0.60 mm | (7.1, 6.3, 3.0) | 2 | 0.0 | 0.5 | 0.05 |
| 6 | taper | 0.73 mm | (15.7, -14.7, 0.0) | 1 | 0.0 | 0.0 | 0.16 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
