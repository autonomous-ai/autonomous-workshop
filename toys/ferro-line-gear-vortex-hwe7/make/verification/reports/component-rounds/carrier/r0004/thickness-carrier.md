# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/part_carrier.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/measure/component-rounds/carrier/r0004/thickness-carrier.md`

part_carrier.step.py: 79.98 cm3 solid, grid 0.430 mm (442x442x59), 294760 surface samples, thickness resolved to 0.215 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.22) | PASS | 0.0% of surface below (52 of 294760 samples); thinnest 0.43 mm at (-1.9, -31.5, 23.5) in 16 region(s); no region is a wall, 16 taper(s) at feature edges (0.01% of surface, budget 2%); 8 more within measurement error of the limit |
| thickness distribution | PASS | median 3.01 mm, p95 5.16 mm, max 86.00 mm |
| hollowable at 1.20 mm wall | WARN | 10.90 of 79.98 cm3 (14%) in 1 pocket(s), 2 too small to shell |
| filament that would save | PASS | 1.64 cm3, 2.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.43 mm | (-39.4, 0.4, 13.5) | 5 | 0.7 | 1.0 | 0.67 |
| 2 | taper | 0.43 mm | (-3.8, 53.4, 13.5) | 6 | 0.5 | 2.1 | 0.26 |
| 3 | taper | 0.43 mm | (23.1, 41.0, 13.5) | 4 | 0.5 | 1.4 | 0.36 |
| 4 | taper | 0.43 mm | (-1.9, -31.5, 23.5) | 4 | 0.5 | 1.7 | 0.28 |
| 5 | taper | 0.43 mm | (1.4, 30.5, 23.5) | 5 | 0.4 | 1.1 | 0.36 |
| 6 | taper | 0.43 mm | (59.6, -24.0, 13.5) | 4 | 0.4 | 0.6 | 0.71 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
