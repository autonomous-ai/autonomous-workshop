# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_coupon_receiver_55.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/coupon_receiver_55/r0001/thickness-coupon_receiver_55.md`

part_coupon_receiver_55.step.py: 0.79 cm3 solid, grid 0.133 mm (173x113x63), 45234 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (8 of 45234 samples); thinnest 0.13 mm at (2.1, -1.9, 4.5) in 5 region(s); no region is a wall, 5 taper(s) at feature edges (0.02% of surface, budget 2%); 5 more within measurement error of the limit |
| thickness distribution | PASS | median 2.80 mm, p95 9.93 mm, max 22.20 mm |
| hollowable at 1.20 mm wall | WARN | 0.04 of 0.79 cm3 (6%) in 1 pocket(s), 2 too small to shell |
| filament that would save | PASS | 0.01 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.33 mm | (-4.4, 5.7, 7.5) | 4 | 0.1 | 0.3 | 0.27 |
| 2 | taper | 0.73 mm | (-4.4, -5.6, 7.6) | 1 | 0.0 | 0.0 | 0.13 |
| 3 | taper | 0.13 mm | (2.8, 0.4, 4.5) | 1 | 0.0 | 0.0 | 0.13 |
| 4 | taper | 0.13 mm | (2.1, -1.9, 4.5) | 1 | 0.0 | 0.0 | 0.13 |
| 5 | taper | 0.33 mm | (2.1, 1.9, 4.5) | 1 | 0.0 | 0.0 | 0.13 |

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
