# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_bear_body.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/bear_body/r0009/thickness-bear_body.md`

part_bear_body.step.py: 23.69 cm3 solid, grid 0.251 mm (307x311x121), 218648 surface samples, thickness resolved to 0.126 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.13) | PASS | 0.0% of surface below (46 of 218648 samples); thinnest 0.38 mm at (-1.6, 26.3, 26.8) in 7 region(s); no region is a wall, 7 taper(s) at feature edges (0.02% of surface, budget 2%); 59 more within measurement error of the limit |
| thickness distribution | PASS | median 4.02 mm, p95 40.60 mm, max 82.47 mm |
| hollowable at 1.20 mm wall | WARN | 7.82 of 23.69 cm3 (33%) in 1 pocket(s) |
| filament that would save | PASS | 1.17 cm3, 1.5 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.63 mm | (1.6, 26.3, 26.2) | 12 | 0.9 | 2.3 | 0.37 |
| 2 | taper | 0.38 mm | (-1.6, 34.7, 26.9) | 12 | 0.8 | 2.1 | 0.37 |
| 3 | taper | 0.63 mm | (-7.4, -20.8, 0.3) | 6 | 0.4 | 0.9 | 0.48 |
| 4 | taper | 0.63 mm | (-14.6, -20.8, 0.4) | 5 | 0.4 | 0.9 | 0.42 |
| 5 | taper | 0.38 mm | (1.5, 34.8, 25.0) | 5 | 0.3 | 1.1 | 0.30 |
| 6 | taper | 0.50 mm | (-1.7, 26.3, 24.5) | 4 | 0.3 | 0.3 | 0.75 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
