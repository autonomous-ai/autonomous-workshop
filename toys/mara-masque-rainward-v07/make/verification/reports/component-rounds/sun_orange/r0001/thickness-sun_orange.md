# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_sun_orange.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/sun_orange/r0001/thickness-sun_orange.md`

part_sun_orange.step.py: 91.76 cm3 solid, grid 0.291 mm (659x647x26), 359043 surface samples, thickness resolved to 0.146 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.15) | PASS | 0.0% of surface below (161 of 359043 samples); thinnest 0.29 mm at (69.7, 48.1, 4.7) in 66 region(s); no region is a wall, 60 taper(s) at feature edges and 6 spot(s) too small to be a wall (0.02% of surface, budget 2%); 195 more within measurement error of the limit |
| thickness distribution | PASS | median 3.78 mm, p95 11.93 mm, max 185.11 mm |
| hollowable at 1.20 mm wall | WARN | 34.97 of 91.76 cm3 (38%) in 1 pocket(s), 2 too small to shell |
| filament that would save | PASS | 5.25 cm3, 6.5 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.58 mm | (-22.4, -16.7, 5.3) | 5 | 0.7 | 3.3 | 0.20 |
| 2 | spot | 0.29 mm | (78.2, 15.6, 5.1) | 9 | 0.6 | 0.6 | 1.13 |
| 3 | spot | 0.58 mm | (31.8, -73.1, 5.3) | 1 | 0.5 | 0.0 | 1.81 |
| 4 | spot | 0.58 mm | (-36.3, 70.9, 5.3) | 1 | 0.5 | 0.0 | 1.78 |
| 5 | spot | 0.29 mm | (-17.7, 77.7, 5.3) | 1 | 0.5 | 0.0 | 1.72 |
| 6 | spot | 0.58 mm | (-32.9, 72.6, 5.1) | 1 | 0.4 | 0.0 | 1.33 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
