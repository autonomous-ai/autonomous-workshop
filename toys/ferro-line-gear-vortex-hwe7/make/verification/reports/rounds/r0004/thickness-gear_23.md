# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/part_gear_23.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/measure/rounds/r0004/thickness-gear_23.md`

part_gear_23.step.py: 3.08 cm3 solid, grid 0.133 mm (282x282x42), 166801 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (10 of 166801 samples); thinnest 0.20 mm at (12.3, 11.6, 5.0) in 9 region(s); no region is a wall, 9 taper(s) at feature edges (0.00% of surface, budget 2%); 1 more within measurement error of the limit |
| thickness distribution | PASS | median 4.73 mm, p95 7.47 mm, max 16.20 mm |
| hollowable at 1.20 mm wall | WARN | 0.38 of 3.08 cm3 (12%) in 1 pocket(s), 102 too small to shell |
| filament that would save | PASS | 0.06 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.40 mm | (-17.0, 3.3, 5.0) | 2 | 0.0 | 1.0 | 0.03 |
| 2 | taper | 0.27 mm | (17.3, 4.0, 5.0) | 1 | 0.0 | 0.0 | 0.09 |
| 3 | taper | 0.73 mm | (-10.9, 14.1, 0.0) | 1 | 0.0 | 0.0 | 0.09 |
| 4 | taper | 0.27 mm | (4.5, 16.7, 5.0) | 1 | 0.0 | 0.0 | 0.09 |
| 5 | taper | 0.73 mm | (16.4, -5.6, 0.0) | 1 | 0.0 | 0.0 | 0.09 |
| 6 | taper | 0.53 mm | (4.5, -16.7, 4.9) | 1 | 0.0 | 0.0 | 0.09 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
