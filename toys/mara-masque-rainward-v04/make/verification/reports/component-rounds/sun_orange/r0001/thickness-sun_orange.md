# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_sun_orange.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/sun_orange/r0001/thickness-sun_orange.md`

part_sun_orange.step.py: 177.32 cm3 solid, grid 0.321 mm (600x601x33), 359709 surface samples, thickness resolved to 0.160 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.16) | PASS | 0.0% of surface below (64 of 359709 samples); thinnest 0.32 mm at (12.7, -89.3, 7.9) in 43 region(s); no region is a wall, 42 taper(s) at feature edges and 1 spot(s) too small to be a wall (0.01% of surface, budget 2%); 789 more within measurement error of the limit |
| thickness distribution | PASS | median 6.10 mm, p95 74.61 mm, max 192.21 mm |
| hollowable at 1.20 mm wall | WARN | 98.49 of 177.32 cm3 (56%) in 1 pocket(s), 7 too small to shell |
| filament that would save | PASS | 14.77 cm3, 18.3 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | spot | 0.32 mm | (12.2, -83.6, 7.8) | 2 | 0.7 | 0.1 | 2.20 |
| 2 | taper | 0.32 mm | (12.7, -89.3, 7.9) | 11 | 0.3 | 1.0 | 0.36 |
| 3 | taper | 0.32 mm | (82.5, 18.2, 7.8) | 2 | 0.2 | 0.8 | 0.32 |
| 4 | taper | 0.32 mm | (-90.2, 6.1, 7.8) | 1 | 0.2 | 0.0 | 0.58 |
| 5 | taper | 0.48 mm | (8.8, -69.3, 8.7) | 5 | 0.2 | 1.5 | 0.12 |
| 6 | taper | 0.32 mm | (-69.0, 53.5, 7.8) | 1 | 0.2 | 0.0 | 0.56 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
