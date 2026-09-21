# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_sun_orange.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/sun_orange/r0005/thickness-sun_orange.md`

part_sun_orange.step.py: 92.15 cm3 solid, grid 0.291 mm (646x652x26), 360840 surface samples, thickness resolved to 0.146 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.15) | PASS | 0.0% of surface below (58 of 360840 samples); thinnest 0.29 mm at (-31.6, 75.7, 5.0) in 45 region(s); no region is a wall, 41 taper(s) at feature edges and 4 spot(s) too small to be a wall (0.01% of surface, budget 2%); 150 more within measurement error of the limit |
| thickness distribution | PASS | median 3.78 mm, p95 11.64 mm, max 179.14 mm |
| hollowable at 1.20 mm wall | WARN | 34.28 of 92.15 cm3 (37%) in 1 pocket(s), 42 too small to shell |
| filament that would save | PASS | 5.14 cm3, 6.4 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.58 mm | (16.7, 21.1, 5.3) | 5 | 0.7 | 3.0 | 0.23 |
| 2 | spot | 0.29 mm | (-58.0, 54.6, 5.3) | 1 | 0.4 | 0.0 | 1.23 |
| 3 | spot | 0.44 mm | (-64.7, 46.5, 5.3) | 1 | 0.3 | 0.0 | 1.18 |
| 4 | spot | 0.58 mm | (-22.3, 16.7, 5.3) | 2 | 0.3 | 0.1 | 0.98 |
| 5 | taper | 0.58 mm | (-10.0, 25.0, 5.4) | 2 | 0.3 | 1.0 | 0.28 |
| 6 | taper | 0.58 mm | (-25.2, -10.0, 5.4) | 2 | 0.3 | 0.8 | 0.34 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
