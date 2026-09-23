# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_bull_body.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/bull_body/r0006/thickness-bull_body.md`

part_bull_body.step.py: 29.28 cm3 solid, grid 0.251 mm (315x303x121), 241541 surface samples, thickness resolved to 0.126 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.13) | PASS | 0.1% of surface below (136 of 241541 samples); thinnest 0.25 mm at (-1.6, 25.3, 27.1) in 12 region(s); no region is a wall, 12 taper(s) at feature edges (0.06% of surface, budget 2%); 100 more within measurement error of the limit |
| thickness distribution | PASS | median 4.27 mm, p95 34.44 mm, max 77.44 mm |
| hollowable at 1.20 mm wall | WARN | 11.28 of 29.28 cm3 (39%) in 1 pocket(s) |
| filament that would save | PASS | 1.69 cm3, 2.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.25 mm | (-1.6, 33.7, 26.5) | 18 | 1.2 | 2.5 | 0.48 |
| 2 | taper | 0.25 mm | (-25.4, -21.8, 18.4) | 16 | 1.1 | 1.5 | 0.75 |
| 3 | taper | 0.38 mm | (-25.4, -29.2, 19.1) | 12 | 1.0 | 2.3 | 0.45 |
| 4 | taper | 0.38 mm | (-28.5, -21.8, 18.1) | 14 | 0.9 | 2.2 | 0.43 |
| 5 | taper | 0.25 mm | (-28.5, -29.2, 18.1) | 13 | 0.9 | 2.6 | 0.34 |
| 6 | taper | 0.38 mm | (25.5, -29.2, 18.4) | 11 | 0.8 | 1.7 | 0.45 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
