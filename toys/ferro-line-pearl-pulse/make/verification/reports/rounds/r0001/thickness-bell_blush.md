# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_bell_blush.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/thickness-bell_blush.md`

part_bell_blush.step.py: 0.30 cm3 solid, grid 0.133 mm (126x196x140), 30202 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 1.1% of surface below (348 of 30202 samples); thinnest 0.13 mm at (19.6, 31.4, 17.6) in 13 region(s); no region is a wall, 13 taper(s) at feature edges (1.11% of surface, budget 2%); 79 more within measurement error of the limit |
| thickness distribution | PASS | median 1.20 mm, p95 6.53 mm, max 12.80 mm |
| hollowable at 1.20 mm wall | PASS | 0.00 of 0.30 cm3 (0%) in 0 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.40 mm | (17.0, 36.8, 18.0) | 276 | 4.8 | 9.7 | 0.50 |
| 2 | taper | 0.20 mm | (11.3, 34.7, 15.0) | 28 | 0.7 | 4.4 | 0.15 |
| 3 | taper | 0.13 mm | (19.6, 31.4, 17.6) | 28 | 0.6 | 3.7 | 0.15 |
| 4 | taper | 0.33 mm | (15.4, 24.8, 3.0) | 3 | 0.1 | 0.1 | 0.43 |
| 5 | taper | 0.33 mm | (10.0, 30.6, 9.1) | 3 | 0.1 | 0.3 | 0.18 |
| 6 | taper | 0.73 mm | (18.7, 29.9, 13.8) | 2 | 0.0 | 0.1 | 0.34 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
