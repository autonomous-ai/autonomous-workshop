# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_bull_body.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/bull_body/r0009/thickness-bull_body.md`

part_bull_body.step.py: 28.11 cm3 solid, grid 0.291 mm (369x286x105), 165652 surface samples, thickness resolved to 0.146 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.15) | FAIL | 0.1% of surface below (190 of 165652 samples); thinnest 0.29 mm at (-36.5, -25.7, 19.2) in 16 region(s); 1 wall(s) (widest band 0.85 mm), 13 taper(s) at feature edges and 2 spot(s) too small to be a wall (0.11% of surface, budget 2%); 88 more within measurement error of the limit |
| thickness distribution | PASS | median 4.22 mm, p95 27.94 mm, max 85.13 mm |
| hollowable at 1.20 mm wall | WARN | 12.20 of 28.11 cm3 (43%) in 1 pocket(s) |
| filament that would save | PASS | 1.83 cm3, 2.3 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.29 mm | (-11.1, -14.8, 0.9) | 23 | 2.3 | 4.4 | 0.52 |
| 2 | taper | 0.29 mm | (-39.6, -18.3, 20.2) | 22 | 2.1 | 4.2 | 0.51 |
| 3 | wall | 0.29 mm | (-39.5, -25.7, 19.4) | 21 | 2.1 | 2.4 | 0.85 |
| 4 | taper | 0.29 mm | (17.7, -25.6, 20.0) | 18 | 1.7 | 2.5 | 0.68 |
| 5 | spot | 0.29 mm | (11.3, -14.9, 0.8) | 11 | 1.5 | 1.5 | 0.99 |
| 6 | taper | 0.29 mm | (17.7, -18.4, 18.9) | 15 | 1.4 | 2.0 | 0.72 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
