# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_sun_orange.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/sun_orange/r0002/thickness-sun_orange.md`

part_sun_orange.step.py: 91.54 cm3 solid, grid 0.291 mm (644x640x26), 359875 surface samples, thickness resolved to 0.146 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.15) | PASS | 0.0% of surface below (58 of 359875 samples); thinnest 0.29 mm at (-74.2, 32.0, 5.0) in 41 region(s); no region is a wall, 31 taper(s) at feature edges and 10 spot(s) too small to be a wall (0.02% of surface, budget 2%); 219 more within measurement error of the limit |
| thickness distribution | PASS | median 3.78 mm, p95 11.93 mm, max 183.51 mm |
| hollowable at 1.20 mm wall | WARN | 34.41 of 91.54 cm3 (38%) in 1 pocket(s), 10 too small to shell |
| filament that would save | PASS | 5.16 cm3, 6.4 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.44 mm | (-3.3, 26.0, 6.2) | 7 | 0.9 | 4.7 | 0.20 |
| 2 | taper | 0.44 mm | (36.2, 71.6, 5.0) | 2 | 0.6 | 1.4 | 0.39 |
| 3 | spot | 0.58 mm | (-69.4, -39.3, 5.3) | 1 | 0.4 | 0.0 | 1.45 |
| 4 | spot | 0.58 mm | (21.0, 76.9, 5.3) | 1 | 0.4 | 0.0 | 1.45 |
| 5 | spot | 0.58 mm | (64.7, -47.1, 5.0) | 1 | 0.4 | 0.0 | 1.42 |
| 6 | spot | 0.29 mm | (45.9, 65.2, 5.3) | 1 | 0.4 | 0.0 | 1.41 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
