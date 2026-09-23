# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_coupon_ball.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/coupon_ball/r0001/thickness-coupon_ball.md`

part_coupon_ball.step.py: 0.62 cm3 solid, grid 0.133 mm (188x72x50), 31453 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.3% of surface below (96 of 31453 samples); thinnest 0.13 mm at (0.9, -4.4, 0.0) in 13 region(s); no region is a wall, 13 taper(s) at feature edges (0.31% of surface, budget 2%); 39 more within measurement error of the limit |
| thickness distribution | PASS | median 5.93 mm, p95 8.00 mm, max 24.40 mm |
| hollowable at 1.20 mm wall | WARN | 0.15 of 0.62 cm3 (23%) in 2 pocket(s) |
| filament that would save | PASS | 0.02 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.20 mm | (-4.3, 1.3, 0.1) | 22 | 0.4 | 5.4 | 0.07 |
| 2 | taper | 0.27 mm | (2.0, 3.9, 0.0) | 20 | 0.4 | 5.0 | 0.07 |
| 3 | taper | 0.13 mm | (0.9, -4.4, 0.0) | 18 | 0.3 | 4.0 | 0.07 |
| 4 | taper | 0.40 mm | (11.2, -2.1, 0.0) | 8 | 0.1 | 2.1 | 0.07 |
| 5 | taper | 0.27 mm | (3.4, -2.8, 0.0) | 4 | 0.1 | 0.8 | 0.19 |
| 6 | taper | 0.67 mm | (5.5, -2.0, 0.0) | 5 | 0.1 | 1.7 | 0.06 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
