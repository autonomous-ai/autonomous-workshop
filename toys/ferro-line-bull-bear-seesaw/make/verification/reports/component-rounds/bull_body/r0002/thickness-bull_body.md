# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_bull_body.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/bull_body/r0002/thickness-bull_body.md`

part_bull_body.step.py: 35.77 cm3 solid, grid 0.251 mm (315x303x121), 263619 surface samples, thickness resolved to 0.126 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.13) | PASS | 0.1% of surface below (157 of 263619 samples); thinnest 0.25 mm at (-1.6, 25.8, 24.9) in 12 region(s); no region is a wall, 12 taper(s) at feature edges (0.06% of surface, budget 2%); 92 more within measurement error of the limit |
| thickness distribution | PASS | median 5.91 mm, p95 39.98 mm, max 81.33 mm |
| hollowable at 1.20 mm wall | WARN | 15.76 of 35.77 cm3 (44%) in 1 pocket(s), 1 too small to shell |
| filament that would save | PASS | 2.36 cm3, 2.9 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.25 mm | (-1.6, 25.8, 24.9) | 26 | 1.8 | 2.7 | 0.68 |
| 2 | taper | 0.25 mm | (28.6, -31.2, 19.4) | 20 | 1.4 | 2.5 | 0.58 |
| 3 | taper | 0.25 mm | (1.5, 33.2, 25.8) | 17 | 1.3 | 2.4 | 0.54 |
| 4 | taper | 0.25 mm | (-25.4, -23.8, 19.2) | 17 | 1.2 | 2.1 | 0.55 |
| 5 | taper | 0.25 mm | (25.6, -31.2, 18.5) | 13 | 0.9 | 2.5 | 0.35 |
| 6 | taper | 0.25 mm | (-28.5, -23.8, 18.4) | 12 | 0.8 | 2.2 | 0.35 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
