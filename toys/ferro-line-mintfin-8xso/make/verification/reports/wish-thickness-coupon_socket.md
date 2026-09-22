# Thickness and hollow

`artifacts/make/r0001/product/mintfin/part_coupon_socket.step.py --nozzle .4 --min-wall 1.2 --report artifacts/make/r0001/product/mintfin/measure/wish-thickness-coupon_socket.md`

part_coupon_socket.step.py: 2.08 cm3 solid, grid 0.200 mm (143x94x51), 40696 surface samples, thickness resolved to 0.100 mm

| check | status | detail |
|---|---|---|
| wall >= 1.20 mm (+/-0.10) | PASS | 0.2% of surface below (80 of 40696 samples); thinnest 0.20 mm at (-0.6, 6.4, 5.3) in 12 region(s); no region is a wall, 12 taper(s) at feature edges (0.20% of surface, budget 2%); 19 more within measurement error of the limit |
| thickness distribution | PASS | median 3.50 mm, p95 27.60 mm, max 27.60 mm |
| hollowable at 1.20 mm wall | WARN | 0.35 of 2.08 cm3 (17%) in 1 pocket(s) |
| filament that would save | PASS | 0.05 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.60 mm | (1.6, 3.5, 9.3) | 30 | 1.3 | 8.7 | 0.15 |
| 2 | taper | 0.20 mm | (-0.6, 6.4, 5.3) | 15 | 0.7 | 4.1 | 0.17 |
| 3 | taper | 0.80 mm | (-3.0, -3.0, 9.3) | 10 | 0.5 | 2.2 | 0.22 |
| 4 | taper | 1.00 mm | (-6.4, 0.3, 6.5) | 5 | 0.2 | 3.4 | 0.07 |
| 5 | taper | 1.00 mm | (2.4, -3.6, 9.3) | 4 | 0.2 | 2.9 | 0.06 |
| 6 | taper | 1.00 mm | (0.6, -4.4, 9.3) | 4 | 0.2 | 0.8 | 0.19 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
