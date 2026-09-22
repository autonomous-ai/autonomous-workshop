# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/part_pedestal.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/measure/component-rounds/pedestal/r0001/thickness-pedestal.md`

part_pedestal.step.py: 35.59 cm3 solid, grid 0.251 mm (422x422x60), 371625 surface samples, thickness resolved to 0.126 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.13) | PASS | 0.1% of surface below (275 of 371625 samples); thinnest 0.25 mm at (8.9, -1.2, 6.3) in 9 region(s); no region is a wall, 9 taper(s) at feature edges (0.07% of surface, budget 2%); 1081 more within measurement error of the limit |
| thickness distribution | PASS | median 2.89 mm, p95 13.83 mm, max 46.89 mm |
| hollowable at 1.20 mm wall | WARN | 4.98 of 35.59 cm3 (14%) in 5 pocket(s) |
| filament that would save | PASS | 0.75 cm3, 0.9 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.50 mm | (-31.3, -42.1, 9.8) | 72 | 5.2 | 7.8 | 0.66 |
| 2 | taper | 0.50 mm | (-20.5, 48.3, 13.7) | 72 | 5.1 | 7.8 | 0.65 |
| 3 | taper | 0.50 mm | (-20.8, -47.3, 9.5) | 64 | 4.6 | 7.7 | 0.59 |
| 4 | taper | 0.50 mm | (-30.4, 41.8, 12.3) | 32 | 2.3 | 7.3 | 0.32 |
| 5 | taper | 0.63 mm | (51.4, 6.0, 11.3) | 18 | 1.3 | 6.6 | 0.20 |
| 6 | taper | 0.63 mm | (51.4, -6.0, 12.5) | 14 | 1.1 | 6.9 | 0.15 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
