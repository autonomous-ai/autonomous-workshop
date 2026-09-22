# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_body_02_front.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/body_02_front/r0001/thickness-body_02_front.md`

part_body_02_front.step.py: 6.25 cm3 solid, grid 0.140 mm (430x327x75), 242043 surface samples, thickness resolved to 0.070 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 3.4% of surface below (8099 of 242043 samples); thinnest 0.14 mm at (-0.2, 21.4, 2.1) in 8 region(s); 2 wall(s) (widest band 5.24 mm), 6 taper(s) at feature edges (0.01% of surface, budget 2%); 97 more within measurement error of the limit |
| thickness distribution | PASS | median 3.15 mm, p95 10.71 mm, max 59.57 mm |
| hollowable at 1.20 mm wall | WARN | 1.12 of 6.25 cm3 (18%) in 1 pocket(s) |
| filament that would save | PASS | 0.17 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.14 mm | (12.2, -14.8, 3.1) | 7731 | 158.8 | 30.3 | 5.24 |
| 2 | wall | 0.14 mm | (-0.2, 21.4, 2.1) | 356 | 7.4 | 4.3 | 1.72 |
| 3 | taper | 0.42 mm | (18.0, -15.1, 2.4) | 5 | 0.1 | 0.9 | 0.14 |
| 4 | taper | 0.56 mm | (-17.9, -15.1, 2.4) | 3 | 0.1 | 0.9 | 0.09 |
| 5 | taper | 0.28 mm | (19.5, 17.1, 0.0) | 1 | 0.0 | 0.0 | 0.21 |
| 6 | taper | 0.56 mm | (-15.8, -14.7, 2.7) | 1 | 0.0 | 0.0 | 0.19 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
