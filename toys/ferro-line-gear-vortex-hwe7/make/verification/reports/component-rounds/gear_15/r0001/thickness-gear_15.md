# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/part_gear_15.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/measure/component-rounds/gear_15/r0001/thickness-gear_15.md`

part_gear_15.step.py: 1.55 cm3 solid, grid 0.133 mm (191x192x42), 89438 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (21 of 89438 samples); thinnest 0.13 mm at (9.7, -5.4, 0.0) in 19 region(s); no region is a wall, 19 taper(s) at feature edges (0.02% of surface, budget 2%); 2 more within measurement error of the limit |
| thickness distribution | PASS | median 3.87 mm, p95 7.00 mm, max 14.73 mm |
| hollowable at 1.20 mm wall | WARN | 0.15 of 1.55 cm3 (10%) in 1 pocket(s), 15 too small to shell |
| filament that would save | PASS | 0.02 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.47 mm | (-11.1, -3.3, 0.0) | 2 | 0.0 | 0.4 | 0.07 |
| 2 | taper | 0.20 mm | (-4.9, 10.4, 0.0) | 2 | 0.0 | 0.7 | 0.02 |
| 3 | taper | 0.67 mm | (-6.5, -9.5, 0.0) | 1 | 0.0 | 0.0 | 0.12 |
| 4 | taper | 0.67 mm | (-6.5, -9.4, 4.9) | 1 | 0.0 | 0.0 | 0.12 |
| 5 | taper | 0.13 mm | (9.7, -5.4, 0.0) | 1 | 0.0 | 0.0 | 0.11 |
| 6 | taper | 0.40 mm | (-2.2, -10.9, 0.0) | 1 | 0.0 | 0.0 | 0.11 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
