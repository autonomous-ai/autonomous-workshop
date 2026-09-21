# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_sun_orange.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/thickness-sun_orange.md`

part_sun_orange.step.py: 173.90 cm3 solid, grid 0.321 mm (600x605x33), 364673 surface samples, thickness resolved to 0.160 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.16) | PASS | 0.0% of surface below (77 of 364673 samples); thinnest 0.32 mm at (86.6, 8.8, 0.0) in 20 region(s); no region is a wall, 18 taper(s) at feature edges and 2 spot(s) too small to be a wall (0.00% of surface, budget 2%); 675 more within measurement error of the limit |
| thickness distribution | PASS | median 6.10 mm, p95 62.89 mm, max 192.37 mm |
| hollowable at 1.20 mm wall | WARN | 96.49 of 173.90 cm3 (55%) in 2 pocket(s), 27 too small to shell |
| filament that would save | PASS | 14.47 cm3, 17.9 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | spot | 0.48 mm | (-65.8, -8.3, 8.4) | 1 | 0.8 | 0.0 | 2.51 |
| 2 | taper | 0.48 mm | (89.4, 26.4, 5.6) | 3 | 0.4 | 0.6 | 0.64 |
| 3 | spot | 0.48 mm | (-8.3, 60.3, 8.4) | 1 | 0.4 | 0.0 | 1.11 |
| 4 | taper | 0.32 mm | (90.4, -22.3, 5.7) | 2 | 0.3 | 0.4 | 0.68 |
| 5 | taper | 0.32 mm | (-18.5, -82.5, 7.8) | 1 | 0.2 | 0.0 | 0.70 |
| 6 | taper | 0.32 mm | (3.6, -84.4, 7.8) | 1 | 0.2 | 0.0 | 0.54 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
