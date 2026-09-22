# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_coupon_socket.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/rounds/r0001/thickness-coupon_socket.md`

part_coupon_socket.step.py: 2.08 cm3 solid, grid 0.133 mm (213x138x74), 94256 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (43 of 94256 samples); thinnest 0.13 mm at (6.6, 0.4, 5.3) in 17 region(s); no region is a wall, 17 taper(s) at feature edges (0.05% of surface, budget 2%); 52 more within measurement error of the limit |
| thickness distribution | PASS | median 3.53 mm, p95 27.67 mm, max 27.73 mm |
| hollowable at 1.20 mm wall | WARN | 0.35 of 2.08 cm3 (17%) in 1 pocket(s) |
| filament that would save | PASS | 0.05 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.67 mm | (6.5, 0.3, 7.8) | 6 | 0.1 | 1.8 | 0.07 |
| 2 | taper | 0.67 mm | (6.5, -0.7, 7.5) | 5 | 0.1 | 1.1 | 0.09 |
| 3 | taper | 0.47 mm | (6.6, -0.8, 5.8) | 5 | 0.1 | 1.2 | 0.08 |
| 4 | taper | 0.67 mm | (-2.5, -3.2, 9.3) | 5 | 0.1 | 1.1 | 0.09 |
| 5 | taper | 0.13 mm | (6.6, 0.4, 5.3) | 4 | 0.1 | 0.2 | 0.40 |
| 6 | taper | 0.13 mm | (-3.0, 3.0, 6.9) | 3 | 0.1 | 0.5 | 0.10 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
