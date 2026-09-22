# Thickness and hollow

`artifacts/make/r0001/product/mintfin/part_coupon_ball.step.py --nozzle .4 --min-wall 1.2 --report artifacts/make/r0001/product/mintfin/measure/wish-thickness-coupon_ball.md`

part_coupon_ball.step.py: 0.62 cm3 solid, grid 0.200 mm (127x50x35), 13840 surface samples, thickness resolved to 0.100 mm

| check | status | detail |
|---|---|---|
| wall >= 1.20 mm (+/-0.10) | PASS | 0.9% of surface below (131 of 13840 samples); thinnest 0.20 mm at (2.4, -3.7, 0.0) in 4 region(s); no region is a wall, 4 taper(s) at feature edges (0.89% of surface, budget 2%); 9 more within measurement error of the limit |
| thickness distribution | PASS | median 5.90 mm, p95 8.00 mm, max 24.40 mm |
| hollowable at 1.20 mm wall | WARN | 0.14 of 0.62 cm3 (23%) in 2 pocket(s) |
| filament that would save | PASS | 0.02 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.20 mm | (4.3, 2.1, 0.0) | 72 | 2.8 | 16.7 | 0.17 |
| 2 | taper | 0.20 mm | (2.4, -3.7, 0.0) | 47 | 1.7 | 10.2 | 0.17 |
| 3 | taper | 0.20 mm | (11.7, -2.1, 0.1) | 9 | 0.4 | 3.1 | 0.12 |
| 4 | taper | 0.80 mm | (6.6, -1.9, 0.0) | 3 | 0.1 | 1.3 | 0.10 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
