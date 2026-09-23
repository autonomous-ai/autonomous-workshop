# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/part_gear_cap.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/measure/component-rounds/gear_cap/r0001/thickness-gear_cap.md`

part_gear_cap.step.py: 0.14 cm3 solid, grid 0.133 mm (59x59x41), 11372 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 2.2% of surface below (212 of 11372 samples); thinnest 0.13 mm at (-0.1, 2.0, 0.0) in 3 region(s); no region is a wall, 3 taper(s) at feature edges (2.19% of surface, budget 2%) -- OVER BUDGET; 22 more within measurement error of the limit |
| thickness distribution | PASS | median 1.80 mm, p95 4.80 mm, max 4.80 mm |
| hollowable at 1.20 mm wall | PASS | 0.00 of 0.14 cm3 (0%) in 0 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (-0.1, 2.0, 0.0) | 104 | 2.5 | 3.8 | 0.66 |
| 2 | taper | 0.13 mm | (0.1, -1.9, 4.7) | 106 | 2.4 | 3.8 | 0.64 |
| 3 | taper | 0.73 mm | (-1.8, 0.6, 4.8) | 2 | 0.0 | 0.1 | 0.26 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
