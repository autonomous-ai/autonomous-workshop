# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_bear_body.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/bear_body/r0002/thickness-bear_body.md`

part_bear_body.step.py: 32.26 cm3 solid, grid 0.251 mm (307x311x121), 240317 surface samples, thickness resolved to 0.126 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.13) | PASS | 0.1% of surface below (141 of 240317 samples); thinnest 0.25 mm at (-1.6, 26.3, 26.5) in 12 region(s); no region is a wall, 12 taper(s) at feature edges (0.06% of surface, budget 2%); 83 more within measurement error of the limit |
| thickness distribution | PASS | median 4.27 mm, p95 50.28 mm, max 82.34 mm |
| hollowable at 1.20 mm wall | WARN | 14.16 of 32.26 cm3 (44%) in 1 pocket(s) |
| filament that would save | PASS | 2.12 cm3, 2.6 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.50 mm | (1.5, 26.3, 24.6) | 18 | 1.4 | 2.4 | 0.59 |
| 2 | taper | 0.25 mm | (28.6, -30.2, 18.9) | 20 | 1.4 | 1.9 | 0.73 |
| 3 | taper | 0.25 mm | (28.6, -22.8, 19.1) | 16 | 1.1 | 2.2 | 0.48 |
| 4 | taper | 0.25 mm | (-28.5, -30.2, 18.5) | 12 | 0.9 | 2.4 | 0.36 |
| 5 | taper | 0.38 mm | (-28.5, -22.8, 19.0) | 12 | 0.8 | 2.6 | 0.32 |
| 6 | taper | 0.25 mm | (-1.6, 26.3, 26.5) | 12 | 0.8 | 1.8 | 0.43 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
