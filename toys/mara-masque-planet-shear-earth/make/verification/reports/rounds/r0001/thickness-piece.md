# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_piece.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/thickness-piece.md`

part_piece.step.py: 9.72 cm3 solid, grid 0.140 mm (247x251x184), 181136 surface samples, thickness resolved to 0.070 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.2% of surface below (323 of 181136 samples); thinnest 0.14 mm at (10.3, 2.1, 15.3) in 39 region(s); no region is a wall, 39 taper(s) at feature edges (0.23% of surface, budget 2%); 48 more within measurement error of the limit |
| thickness distribution | PASS | median 20.93 mm, p95 33.95 mm, max 34.44 mm |
| hollowable at 1.20 mm wall | WARN | 5.67 of 9.72 cm3 (58%) in 1 pocket(s) |
| filament that would save | PASS | 0.85 cm3, 1.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.14 mm | (1.9, 8.7, 6.4) | 61 | 1.7 | 6.3 | 0.26 |
| 2 | taper | 0.14 mm | (2.5, -8.8, 20.3) | 51 | 1.6 | 4.2 | 0.38 |
| 3 | taper | 0.14 mm | (4.5, 7.6, 20.9) | 36 | 0.9 | 3.6 | 0.25 |
| 4 | taper | 0.14 mm | (10.3, 2.1, 15.3) | 20 | 0.6 | 1.2 | 0.53 |
| 5 | taper | 0.14 mm | (-5.7, -6.8, 6.3) | 19 | 0.5 | 4.0 | 0.12 |
| 6 | taper | 0.14 mm | (2.3, 7.3, 22.2) | 15 | 0.4 | 1.9 | 0.21 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
