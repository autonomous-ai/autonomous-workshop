# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_carrier.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/carrier/r0001/thickness-carrier.md`

part_carrier.step.py: 0.97 cm3 solid, grid 0.133 mm (365x413x35), 76928 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 1.4% of surface below (943 of 76928 samples); thinnest 0.73 mm at (-14.7, -24.4, 0.8) in 3 region(s); 3 wall(s) (widest band 2.07 mm); 1168 more within measurement error of the limit |
| thickness distribution | PASS | median 2.00 mm, p95 4.00 mm, max 25.80 mm |
| hollowable at 1.20 mm wall | PASS | 0.00 of 0.97 cm3 (0%) in 0 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.73 mm | (-14.7, -24.4, 0.8) | 319 | 6.8 | 3.3 | 2.06 |
| 2 | wall | 0.73 mm | (-14.0, 24.6, 0.8) | 316 | 6.8 | 3.3 | 2.07 |
| 3 | wall | 0.73 mm | (26.7, 0.2, 0.8) | 308 | 6.8 | 3.3 | 2.07 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
