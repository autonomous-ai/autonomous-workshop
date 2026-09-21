# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_sun_orange.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0002/thickness-sun_orange.md`

part_sun_orange.step.py: 170.88 cm3 solid, grid 0.321 mm (600x605x33), 363528 surface samples, thickness resolved to 0.160 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.16) | PASS | 0.0% of surface below (123 of 363528 samples); thinnest 0.32 mm at (-33.1, -80.9, 7.8) in 21 region(s); no region is a wall, 16 taper(s) at feature edges and 5 spot(s) too small to be a wall (0.01% of surface, budget 2%); 688 more within measurement error of the limit |
| thickness distribution | PASS | median 6.10 mm, p95 57.92 mm, max 192.37 mm |
| hollowable at 1.20 mm wall | WARN | 94.57 of 170.88 cm3 (55%) in 2 pocket(s), 16 too small to shell |
| filament that would save | PASS | 14.19 cm3, 17.6 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | spot | 0.48 mm | (8.3, -66.4, 8.4) | 1 | 0.5 | 0.0 | 1.67 |
| 2 | spot | 0.48 mm | (60.9, 8.4, 8.6) | 1 | 0.5 | 0.0 | 1.67 |
| 3 | spot | 0.48 mm | (-8.9, 69.3, 8.7) | 43 | 0.4 | 0.5 | 0.82 |
| 4 | spot | 0.32 mm | (-41.7, 82.0, 5.3) | 6 | 0.4 | 0.5 | 0.81 |
| 5 | spot | 0.48 mm | (-62.0, -8.6, 8.4) | 2 | 0.3 | 0.1 | 1.06 |
| 6 | taper | 0.48 mm | (-39.5, -86.5, 4.2) | 1 | 0.3 | 0.0 | 0.80 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
