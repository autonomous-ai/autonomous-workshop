# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_coupon_receiver_45.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/coupon_receiver_45/r0001/thickness-coupon_receiver_45.md`

part_coupon_receiver_45.step.py: 0.82 cm3 solid, grid 0.133 mm (173x113x63), 45440 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (8 of 45440 samples); thinnest 0.13 mm at (-4.4, -5.7, 7.4) in 4 region(s); no region is a wall, 4 taper(s) at feature edges (0.02% of surface, budget 2%); 2 more within measurement error of the limit |
| thickness distribution | PASS | median 3.07 mm, p95 10.00 mm, max 22.20 mm |
| hollowable at 1.20 mm wall | WARN | 0.06 of 0.82 cm3 (7%) in 1 pocket(s), 1 too small to shell |
| filament that would save | PASS | 0.01 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.33 mm | (-4.4, 5.7, 7.6) | 5 | 0.1 | 0.7 | 0.14 |
| 2 | taper | 0.33 mm | (-2.0, 2.6, 5.1) | 1 | 0.0 | 0.0 | 0.15 |
| 3 | taper | 0.27 mm | (-2.9, 3.7, 2.4) | 1 | 0.0 | 0.0 | 0.15 |
| 4 | taper | 0.13 mm | (-4.4, -5.7, 7.4) | 1 | 0.0 | 0.0 | 0.14 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
