# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_bull_body.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/thickness-bull_body.md`

part_bull_body.step.py: 31.20 cm3 solid, grid 0.251 mm (315x303x121), 240173 surface samples, thickness resolved to 0.126 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.13) | PASS | 0.1% of surface below (148 of 240173 samples); thinnest 0.25 mm at (-1.5, 25.3, 27.2) in 12 region(s); no region is a wall, 12 taper(s) at feature edges (0.06% of surface, budget 2%); 112 more within measurement error of the limit |
| thickness distribution | PASS | median 4.27 mm, p95 39.85 mm, max 77.44 mm |
| hollowable at 1.20 mm wall | WARN | 13.27 of 31.20 cm3 (43%) in 1 pocket(s) |
| filament that would save | PASS | 1.99 cm3, 2.5 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.25 mm | (28.6, -29.2, 20.5) | 22 | 1.6 | 2.6 | 0.61 |
| 2 | taper | 0.25 mm | (28.6, -21.8, 20.4) | 19 | 1.3 | 2.7 | 0.49 |
| 3 | taper | 0.25 mm | (-25.4, -29.2, 19.4) | 18 | 1.2 | 2.3 | 0.53 |
| 4 | taper | 0.25 mm | (-28.5, -29.2, 17.9) | 13 | 0.9 | 2.4 | 0.39 |
| 5 | taper | 0.38 mm | (1.5, 25.3, 24.9) | 12 | 0.9 | 1.9 | 0.51 |
| 6 | taper | 0.38 mm | (-28.5, -21.8, 18.0) | 13 | 0.8 | 2.5 | 0.33 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
