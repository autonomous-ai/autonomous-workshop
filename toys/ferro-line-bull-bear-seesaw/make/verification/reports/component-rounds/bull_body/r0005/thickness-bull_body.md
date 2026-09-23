# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_bull_body.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/bull_body/r0005/thickness-bull_body.md`

part_bull_body.step.py: 31.40 cm3 solid, grid 0.251 mm (315x303x121), 238741 surface samples, thickness resolved to 0.126 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.13) | PASS | 0.1% of surface below (117 of 238741 samples); thinnest 0.25 mm at (-1.6, 25.3, 26.4) in 12 region(s); no region is a wall, 12 taper(s) at feature edges (0.05% of surface, budget 2%); 124 more within measurement error of the limit |
| thickness distribution | PASS | median 4.27 mm, p95 41.99 mm, max 81.33 mm |
| hollowable at 1.20 mm wall | WARN | 13.38 of 31.40 cm3 (43%) in 1 pocket(s) |
| filament that would save | PASS | 2.01 cm3, 2.5 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.25 mm | (-28.5, -23.8, 18.1) | 14 | 1.0 | 2.4 | 0.43 |
| 2 | taper | 0.38 mm | (-28.5, -31.2, 18.2) | 14 | 1.0 | 2.3 | 0.45 |
| 3 | taper | 0.25 mm | (28.6, -31.2, 18.8) | 15 | 1.0 | 2.7 | 0.37 |
| 4 | taper | 0.38 mm | (28.7, -23.9, 20.6) | 12 | 0.9 | 2.5 | 0.37 |
| 5 | taper | 0.38 mm | (-25.4, -23.8, 18.7) | 10 | 0.9 | 2.6 | 0.32 |
| 6 | taper | 0.25 mm | (-1.6, 25.3, 26.4) | 11 | 0.7 | 2.4 | 0.29 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
