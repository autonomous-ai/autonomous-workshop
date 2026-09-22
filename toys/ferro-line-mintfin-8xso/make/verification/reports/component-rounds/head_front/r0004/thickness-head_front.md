# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_head_front.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/head_front/r0004/thickness-head_front.md`

part_head_front.step.py: 52.27 cm3 solid, grid 0.207 mm (327x227x143), 210565 surface samples, thickness resolved to 0.103 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.10) | PASS | 0.0% of surface below (54 of 210565 samples); thinnest 0.21 mm at (29.0, -10.5, 26.6) in 34 region(s); no region is a wall, 34 taper(s) at feature edges (0.02% of surface, budget 2%); 12 more within measurement error of the limit |
| thickness distribution | PASS | median 24.20 mm, p95 60.19 mm, max 66.60 mm |
| hollowable at 1.20 mm wall | WARN | 41.58 of 52.27 cm3 (80%) in 1 pocket(s) |
| filament that would save | PASS | 6.24 cm3, 7.7 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.31 mm | (12.4, -17.6, 28.1) | 4 | 0.2 | 0.3 | 0.54 |
| 2 | taper | 0.52 mm | (-9.5, 16.1, 20.8) | 3 | 0.1 | 0.4 | 0.30 |
| 3 | taper | 0.41 mm | (-7.3, 15.1, 21.0) | 2 | 0.1 | 0.1 | 0.57 |
| 4 | taper | 0.21 mm | (-28.1, 10.5, 22.0) | 3 | 0.1 | 1.0 | 0.11 |
| 5 | taper | 0.52 mm | (-0.7, 13.1, 21.5) | 3 | 0.1 | 1.6 | 0.06 |
| 6 | taper | 0.52 mm | (-13.0, 4.7, 21.9) | 2 | 0.1 | 0.0 | 0.41 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
