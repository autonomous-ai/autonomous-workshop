# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_head_rear.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/head_rear/r0001/thickness-head_rear.md`

part_head_rear.step.py: 49.38 cm3 solid, grid 0.207 mm (326x227x153), 199457 surface samples, thickness resolved to 0.103 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.10) | PASS | 0.2% of surface below (367 of 199457 samples); thinnest 0.21 mm at (-14.3, 20.8, 0.1) in 35 region(s); no region is a wall, 34 taper(s) at feature edges and 1 spot(s) too small to be a wall (0.21% of surface, budget 2%); 166 more within measurement error of the limit |
| thickness distribution | PASS | median 25.44 mm, p95 46.75 mm, max 65.05 mm |
| hollowable at 1.20 mm wall | WARN | 39.25 of 49.38 cm3 (79%) in 1 pocket(s) |
| filament that would save | PASS | 5.89 cm3, 7.3 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.21 mm | (4.1, 4.3, 30.5) | 107 | 4.8 | 10.0 | 0.48 |
| 2 | taper | 0.21 mm | (-0.8, 10.4, 30.5) | 101 | 4.7 | 10.0 | 0.47 |
| 3 | taper | 0.21 mm | (-1.9, -22.6, 5.7) | 47 | 2.5 | 9.1 | 0.28 |
| 4 | taper | 0.31 mm | (31.0, 4.3, 10.0) | 21 | 1.2 | 4.9 | 0.24 |
| 5 | taper | 0.52 mm | (29.1, 9.0, 8.7) | 5 | 0.7 | 0.9 | 0.76 |
| 6 | spot | 0.52 mm | (-29.1, 9.0, 8.0) | 5 | 0.7 | 0.4 | 1.94 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
