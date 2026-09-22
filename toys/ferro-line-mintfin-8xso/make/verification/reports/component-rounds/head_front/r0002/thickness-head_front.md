# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_head_front.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/head_front/r0002/thickness-head_front.md`

part_head_front.step.py: 52.58 cm3 solid, grid 0.207 mm (327x227x143), 213545 surface samples, thickness resolved to 0.103 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.10) | PASS | 0.1% of surface below (271 of 213545 samples); thinnest 0.21 mm at (-11.4, 17.6, 22.1) in 20 region(s); no region is a wall, 20 taper(s) at feature edges (0.15% of surface, budget 2%); 63 more within measurement error of the limit |
| thickness distribution | PASS | median 24.30 mm, p95 59.88 mm, max 66.60 mm |
| hollowable at 1.20 mm wall | WARN | 41.72 of 52.58 cm3 (79%) in 1 pocket(s) |
| filament that would save | PASS | 6.26 cm3, 7.8 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.21 mm | (-11.4, 17.6, 22.1) | 137 | 6.7 | 9.4 | 0.72 |
| 2 | taper | 0.21 mm | (10.3, 17.2, 23.1) | 114 | 5.9 | 9.1 | 0.65 |
| 3 | taper | 0.41 mm | (-3.0, -10.0, 25.0) | 2 | 0.1 | 1.2 | 0.10 |
| 4 | taper | 0.62 mm | (4.5, -19.7, 28.5) | 2 | 0.1 | 0.2 | 0.56 |
| 5 | taper | 0.21 mm | (-28.9, -7.4, 25.9) | 1 | 0.1 | 0.0 | 0.39 |
| 6 | taper | 0.21 mm | (26.5, 13.9, 21.4) | 1 | 0.1 | 0.0 | 0.31 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
