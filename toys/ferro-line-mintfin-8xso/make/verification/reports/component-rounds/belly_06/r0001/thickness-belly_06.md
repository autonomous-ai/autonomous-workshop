# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_belly_06.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/belly_06/r0001/thickness-belly_06.md`

part_belly_06.step.py: 0.07 cm3 solid, grid 0.133 mm (164x37x14), 8960 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 6.8% of surface below (583 of 8960 samples); thinnest 0.13 mm at (3.6, 2.0, 0.1) in 1 region(s); no region is a wall, 1 taper(s) at feature edges (6.75% of surface, budget 2%) -- OVER BUDGET; 142 more within measurement error of the limit |
| thickness distribution | PASS | median 1.20 mm, p95 2.67 mm, max 3.67 mm |
| hollowable at 1.20 mm wall | PASS | 0.00 of 0.07 cm3 (0%) in 0 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (3.6, 2.0, 0.1) | 583 | 12.1 | 21.5 | 0.56 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
