# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/part_gear_18.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/measure/rounds/r0001/thickness-gear_18.md`

part_gear_18.step.py: 2.09 cm3 solid, grid 0.133 mm (226x224x42), 118236 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (19 of 118236 samples); thinnest 0.13 mm at (7.6, 11.2, 5.0) in 17 region(s); no region is a wall, 17 taper(s) at feature edges (0.01% of surface, budget 2%); 1 more within measurement error of the limit |
| thickness distribution | PASS | median 4.00 mm, p95 7.07 mm, max 12.47 mm |
| hollowable at 1.20 mm wall | WARN | 0.22 of 2.09 cm3 (10%) in 1 pocket(s), 54 too small to shell |
| filament that would save | PASS | 0.03 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.20 mm | (3.3, 12.8, 5.0) | 2 | 0.0 | 0.8 | 0.04 |
| 2 | taper | 0.13 mm | (7.6, 11.2, 5.0) | 2 | 0.0 | 0.0 | 0.16 |
| 3 | taper | 0.47 mm | (12.5, 5.6, 4.9) | 1 | 0.0 | 0.0 | 0.12 |
| 4 | taper | 0.40 mm | (-12.4, 5.5, 0.0) | 1 | 0.0 | 0.0 | 0.12 |
| 5 | taper | 0.53 mm | (12.5, -5.6, 4.9) | 1 | 0.0 | 0.0 | 0.12 |
| 6 | taper | 0.73 mm | (13.2, -1.1, 0.0) | 1 | 0.0 | 0.0 | 0.12 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
