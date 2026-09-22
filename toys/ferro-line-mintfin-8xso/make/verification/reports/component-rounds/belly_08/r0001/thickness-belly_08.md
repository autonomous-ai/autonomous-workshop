# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_belly_08.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/belly_08/r0001/thickness-belly_08.md`

part_belly_08.step.py: 0.02 cm3 solid, grid 0.133 mm (84x23x14), 2980 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.7% of surface below (25 of 2980 samples); thinnest 0.13 mm at (5.2, -0.2, 0.0) in 4 region(s); no region is a wall, 4 taper(s) at feature edges (0.66% of surface, budget 2%); 5 more within measurement error of the limit |
| thickness distribution | PASS | median 1.20 mm, p95 2.20 mm, max 3.33 mm |
| hollowable at 1.20 mm wall | PASS | 0.00 of 0.02 cm3 (0%) in 0 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.27 mm | (-5.2, 0.0, 0.0) | 15 | 0.3 | 0.8 | 0.33 |
| 2 | taper | 0.13 mm | (5.2, -0.2, 0.0) | 8 | 0.1 | 0.4 | 0.22 |
| 3 | taper | 0.33 mm | (0.6, 1.2, 1.2) | 1 | 0.0 | 0.0 | 0.18 |
| 4 | taper | 0.47 mm | (-1.3, -1.0, 1.2) | 1 | 0.0 | 0.0 | 0.14 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
