# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/part_bezel.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/gear_vortex/measure/component-rounds/bezel/r0001/thickness-bezel.md`

part_bezel.step.py: 4.63 cm3 solid, grid 0.133 mm (530x530x35), 207873 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 0.8% of surface below (982 of 207873 samples); thinnest 0.13 mm at (23.6, -25.7, 3.3) in 119 region(s); 2 wall(s) (widest band 1.44 mm), 111 taper(s) at feature edges and 6 spot(s) too small to be a wall (0.55% of surface, budget 2%); 589 more within measurement error of the limit |
| thickness distribution | PASS | median 4.00 mm, p95 6.00 mm, max 29.20 mm |
| hollowable at 1.20 mm wall | WARN | 0.98 of 4.63 cm3 (21%) in 2 pocket(s), 1 too small to shell |
| filament that would save | PASS | 0.15 cm3, 0.2 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.47 mm | (-0.1, -34.2, 1.3) | 239 | 5.5 | 3.8 | 1.44 |
| 2 | wall | 0.40 mm | (0.1, 34.7, 0.4) | 205 | 4.8 | 3.8 | 1.27 |
| 3 | taper | 0.73 mm | (0.2, -29.0, 0.2) | 133 | 2.5 | 3.7 | 0.68 |
| 4 | taper | 0.73 mm | (-0.3, 29.8, 3.2) | 63 | 1.1 | 3.6 | 0.32 |
| 5 | taper | 0.13 mm | (26.2, -23.2, 3.7) | 15 | 0.9 | 2.7 | 0.35 |
| 6 | taper | 0.20 mm | (-32.5, 12.8, 3.7) | 10 | 0.5 | 1.0 | 0.54 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
