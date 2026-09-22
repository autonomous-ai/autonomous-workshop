# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/part_head_front.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/mintfin/measure/component-rounds/head_front/r0003/thickness-head_front.md`

part_head_front.step.py: 52.28 cm3 solid, grid 0.207 mm (327x227x143), 210473 surface samples, thickness resolved to 0.103 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.10) | PASS | 0.0% of surface below (35 of 210473 samples); thinnest 0.21 mm at (-30.4, -7.0, 25.8) in 30 region(s); no region is a wall, 30 taper(s) at feature edges (0.02% of surface, budget 2%); 17 more within measurement error of the limit |
| thickness distribution | PASS | median 24.20 mm, p95 60.09 mm, max 66.60 mm |
| hollowable at 1.20 mm wall | WARN | 41.58 of 52.28 cm3 (80%) in 1 pocket(s) |
| filament that would save | PASS | 6.24 cm3, 7.7 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.21 mm | (-10.1, 16.4, 20.8) | 3 | 0.1 | 0.8 | 0.16 |
| 2 | taper | 0.41 mm | (-7.3, 15.1, 21.1) | 2 | 0.1 | 0.3 | 0.39 |
| 3 | taper | 0.52 mm | (-29.3, 6.7, 22.8) | 2 | 0.1 | 0.0 | 0.40 |
| 4 | taper | 0.21 mm | (-30.4, -7.0, 25.8) | 1 | 0.1 | 0.0 | 0.30 |
| 5 | taper | 0.62 mm | (-24.5, 16.7, 20.8) | 1 | 0.1 | 0.0 | 0.29 |
| 6 | taper | 0.52 mm | (19.2, 2.5, 22.4) | 1 | 0.1 | 0.0 | 0.29 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
