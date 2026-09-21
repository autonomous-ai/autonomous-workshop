# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/veinwake/part_rind.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/veinwake/measure/component-rounds/rind/r0004/thickness-rind.md`

part_rind.step.py: 131.60 cm3 solid, grid 0.291 mm (486x451x53), 380031 surface samples, thickness resolved to 0.146 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.15) | PASS | 0.1% of surface below (280 of 380031 samples); thinnest 0.29 mm at (47.7, -63.5, 0.0) in 49 region(s); no region is a wall, 49 taper(s) at feature edges (0.07% of surface, budget 2%); 175 more within measurement error of the limit |
| thickness distribution | PASS | median 7.86 mm, p95 22.12 mm, max 62.58 mm |
| hollowable at 1.20 mm wall | WARN | 84.75 of 131.60 cm3 (64%) in 1 pocket(s) |
| filament that would save | PASS | 12.71 cm3, 15.8 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.29 mm | (68.7, 9.3, 0.0) | 46 | 4.8 | 27.5 | 0.17 |
| 2 | taper | 0.29 mm | (65.8, -24.5, 0.0) | 26 | 2.7 | 8.5 | 0.32 |
| 3 | taper | 0.29 mm | (57.9, 56.9, 0.0) | 15 | 1.7 | 10.8 | 0.15 |
| 4 | taper | 0.58 mm | (-67.9, -1.1, 0.0) | 16 | 1.7 | 6.3 | 0.26 |
| 5 | taper | 0.44 mm | (65.6, 48.0, 0.3) | 13 | 1.4 | 4.6 | 0.32 |
| 6 | taper | 0.29 mm | (-64.4, 23.1, 0.0) | 13 | 1.4 | 3.8 | 0.36 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
