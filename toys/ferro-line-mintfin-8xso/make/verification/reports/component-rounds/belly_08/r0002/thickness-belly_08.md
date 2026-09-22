# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_belly_08.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/belly_08/r0002/thickness-belly_08.md`

part_belly_08.step.py: 0.00 cm3 solid, grid 0.133 mm (41x12x14), 919 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 21.9% of surface below (228 of 919 samples); thinnest 0.40 mm at (-2.4, -0.1, 0.5) in 2 region(s); no region is a wall, 0 taper(s) at feature edges and 2 spot(s) too small to be a wall (21.95% of surface, budget 2%) -- OVER BUDGET; 17 more within measurement error of the limit |
| thickness distribution | PASS | median 0.93 mm, p95 1.20 mm, max 4.80 mm |
| hollowable at 1.20 mm wall | PASS | 0.00 of 0.00 cm3 (0%) in 0 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | spot | 0.40 mm | (2.3, -0.1, 0.4) | 111 | 2.1 | 1.5 | 1.43 |
| 2 | spot | 0.40 mm | (-2.4, -0.1, 0.5) | 117 | 2.1 | 1.5 | 1.42 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
