# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_belly_01.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/belly_01/r0001/thickness-belly_01.md`

part_belly_01.step.py: 0.36 cm3 solid, grid 0.133 mm (342x72x14), 37593 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 3.2% of surface below (1119 of 37593 samples); thinnest 0.13 mm at (-15.7, -3.2, 0.1) in 1 region(s); no region is a wall, 1 taper(s) at feature edges (3.24% of surface, budget 2%) -- OVER BUDGET; 286 more within measurement error of the limit |
| thickness distribution | PASS | median 1.20 mm, p95 2.40 mm, max 4.67 mm |
| hollowable at 1.20 mm wall | PASS | 0.00 of 0.36 cm3 (0%) in 0 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (-15.7, -3.2, 0.1) | 1119 | 23.1 | 45.8 | 0.51 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
