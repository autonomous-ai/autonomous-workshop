# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/part_coupon.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/measure/component-rounds/coupon/r0001/thickness-coupon.md`

part_coupon.step.py: 2.69 cm3 solid, grid 0.133 mm (350x140x106), 122710 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.2% of surface below (230 of 122710 samples); thinnest 0.13 mm at (14.3, 1.0, 13.3) in 2 region(s); no region is a wall, 2 taper(s) at feature edges (0.21% of surface, budget 2%); 16 more within measurement error of the limit |
| thickness distribution | PASS | median 2.93 mm, p95 18.00 mm, max 46.00 mm |
| hollowable at 1.20 mm wall | WARN | 0.41 of 2.69 cm3 (15%) in 1 pocket(s) |
| filament that would save | PASS | 0.06 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (14.3, 1.0, 13.3) | 116 | 2.5 | 3.2 | 0.79 |
| 2 | taper | 0.13 mm | (-11.3, 1.1, 13.4) | 114 | 2.3 | 3.2 | 0.71 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
