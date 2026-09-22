# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/part_rim_trim.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/measure/component-rounds/rim_trim/r0001/thickness-rim_trim.md`

part_rim_trim.step.py: 0.29 cm3 solid, grid 0.133 mm (747x747x11), 52201 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 30.0% of surface below (16451 of 52201 samples); thinnest 0.73 mm at (-36.2, -33.1, 0.8) in 1 region(s); 1 wall(s) (widest band 2.63 mm); 16346 more within measurement error of the limit |
| thickness distribution | PASS | median 0.80 mm, p95 1.20 mm, max 1.27 mm |
| hollowable at 1.20 mm wall | PASS | 0.00 of 0.29 cm3 (0%) in 0 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.73 mm | (-36.2, -33.1, 0.8) | 16451 | 367.8 | 139.7 | 2.63 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
