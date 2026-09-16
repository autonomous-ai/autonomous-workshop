# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_return_arm.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/return_arm/r0001/thickness-return_arm.md`

part_return_arm.step.py: 0.16 cm3 solid, grid 0.133 mm (41x151x32), 13457 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 2.8% of surface below (359 of 13457 samples); thinnest 0.33 mm at (-0.4, -72.8, 1.9) in 1 region(s); 1 wall(s) (widest band 2.93 mm) |
| thickness distribution | PASS | median 2.40 mm, p95 4.80 mm, max 19.47 mm |
| hollowable at 1.20 mm wall | PASS | 0.00 of 0.16 cm3 (0%) in 0 pocket(s), 1 too small to shell |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.33 mm | (-0.4, -72.8, 1.9) | 359 | 7.8 | 2.7 | 2.93 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
