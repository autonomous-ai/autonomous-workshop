# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/part_axle.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/measure/component-rounds/axle/r0006/thickness-axle.md`

part_axle.step.py: 4.52 cm3 solid, grid 0.140 mm (169x169x394), 273641 surface samples, thickness resolved to 0.070 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (39 of 273641 samples); thinnest 0.28 mm at (2.2, 8.0, 54.3) in 5 region(s); no region is a wall, 5 taper(s) at feature edges (0.04% of surface, budget 2%); 12 more within measurement error of the limit |
| thickness distribution | PASS | median 1.75 mm, p95 4.41 mm, max 54.46 mm |
| hollowable at 1.20 mm wall | WARN | 0.08 of 4.52 cm3 (2%) in 1 pocket(s) |
| filament that would save | PASS | 0.01 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.28 mm | (2.2, 8.0, 54.3) | 21 | 1.3 | 5.2 | 0.24 |
| 2 | taper | 0.35 mm | (4.6, -6.9, 0.3) | 15 | 0.9 | 3.9 | 0.23 |
| 3 | taper | 0.42 mm | (-3.0, -7.6, 54.5) | 1 | 0.0 | 0.0 | 0.32 |
| 4 | taper | 0.70 mm | (7.9, -2.8, 0.5) | 1 | 0.0 | 0.0 | 0.24 |
| 5 | taper | 0.42 mm | (-8.0, 2.0, 0.0) | 1 | 0.0 | 0.0 | 0.21 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
