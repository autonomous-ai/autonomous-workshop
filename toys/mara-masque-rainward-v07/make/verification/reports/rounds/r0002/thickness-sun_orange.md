# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_sun_orange.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0002/thickness-sun_orange.md`

part_sun_orange.step.py: 91.77 cm3 solid, grid 0.291 mm (658x643x26), 359095 surface samples, thickness resolved to 0.146 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.15) | PASS | 0.0% of surface below (139 of 359095 samples); thinnest 0.29 mm at (-10.4, -82.2, 4.5) in 61 region(s); no region is a wall, 53 taper(s) at feature edges and 8 spot(s) too small to be a wall (0.02% of surface, budget 2%); 181 more within measurement error of the limit |
| thickness distribution | PASS | median 3.78 mm, p95 11.93 mm, max 186.42 mm |
| hollowable at 1.20 mm wall | WARN | 34.96 of 91.77 cm3 (38%) in 1 pocket(s), 3 too small to shell |
| filament that would save | PASS | 5.24 cm3, 6.5 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.44 mm | (29.0, 11.6, 5.3) | 4 | 0.5 | 3.3 | 0.17 |
| 2 | spot | 0.29 mm | (62.8, -49.1, 5.3) | 1 | 0.5 | 0.0 | 1.87 |
| 3 | taper | 0.58 mm | (16.0, 21.4, 5.4) | 4 | 0.5 | 2.1 | 0.25 |
| 4 | taper | 0.44 mm | (-10.2, -25.5, 5.4) | 4 | 0.5 | 3.0 | 0.18 |
| 5 | spot | 0.29 mm | (61.5, -50.7, 5.3) | 1 | 0.5 | 0.0 | 1.85 |
| 6 | taper | 0.58 mm | (28.3, 3.4, 5.4) | 4 | 0.5 | 1.5 | 0.37 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
