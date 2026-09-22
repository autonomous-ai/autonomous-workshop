# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/part_gear_20.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/measure/rounds/r0004/thickness-gear_20.md`

part_gear_20.step.py: 2.47 cm3 solid, grid 0.133 mm (249x249x42), 137470 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (16 of 137470 samples); thinnest 0.13 mm at (13.7, -5.6, 0.0) in 13 region(s); no region is a wall, 13 taper(s) at feature edges (0.01% of surface, budget 2%); 2 more within measurement error of the limit |
| thickness distribution | PASS | median 4.27 mm, p95 7.07 mm, max 14.00 mm |
| hollowable at 1.20 mm wall | WARN | 0.27 of 2.47 cm3 (11%) in 1 pocket(s), 76 too small to shell |
| filament that would save | PASS | 0.04 cm3, 0.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.33 mm | (14.6, 5.6, 5.0) | 2 | 0.0 | 0.5 | 0.07 |
| 2 | taper | 0.47 mm | (-14.0, 5.6, 4.9) | 2 | 0.0 | 0.5 | 0.07 |
| 3 | taper | 0.20 mm | (-3.7, 14.6, 5.0) | 2 | 0.0 | 0.5 | 0.04 |
| 4 | taper | 0.47 mm | (-5.6, 14.1, 4.9) | 1 | 0.0 | 0.0 | 0.13 |
| 5 | taper | 0.13 mm | (13.7, -5.6, 0.0) | 1 | 0.0 | 0.0 | 0.12 |
| 6 | taper | 0.27 mm | (13.7, -5.6, 4.9) | 1 | 0.0 | 0.0 | 0.12 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
