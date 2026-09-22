# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_sun_orange.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/sun_orange/r0003/thickness-sun_orange.md`

part_sun_orange.step.py: 92.14 cm3 solid, grid 0.291 mm (646x652x26), 358659 surface samples, thickness resolved to 0.146 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.15) | PASS | 0.0% of surface below (76 of 358659 samples); thinnest 0.29 mm at (79.2, 10.5, 5.0) in 54 region(s); no region is a wall, 47 taper(s) at feature edges and 7 spot(s) too small to be a wall (0.02% of surface, budget 2%); 181 more within measurement error of the limit |
| thickness distribution | PASS | median 3.78 mm, p95 11.64 mm, max 179.29 mm |
| hollowable at 1.20 mm wall | WARN | 34.28 of 92.14 cm3 (37%) in 1 pocket(s), 42 too small to shell |
| filament that would save | PASS | 5.14 cm3, 6.4 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.58 mm | (-4.0, -27.7, 5.4) | 4 | 0.6 | 2.1 | 0.26 |
| 2 | spot | 0.58 mm | (30.9, -3.7, 5.4) | 3 | 0.4 | 0.5 | 0.86 |
| 3 | taper | 0.44 mm | (22.8, 18.0, 5.3) | 3 | 0.4 | 3.3 | 0.13 |
| 4 | taper | 0.58 mm | (-24.9, -19.5, 5.4) | 3 | 0.4 | 3.8 | 0.11 |
| 5 | taper | 0.58 mm | (17.8, -23.8, 5.4) | 3 | 0.4 | 1.5 | 0.28 |
| 6 | spot | 0.29 mm | (76.6, 21.9, 5.3) | 1 | 0.4 | 0.0 | 1.25 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
