# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_piece.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/piece/r0005/thickness-piece.md`

part_piece.step.py: 9.72 cm3 solid, grid 0.140 mm (247x251x184), 181335 surface samples, thickness resolved to 0.070 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.2% of surface below (305 of 181335 samples); thinnest 0.14 mm at (10.4, 2.1, 15.5) in 53 region(s); no region is a wall, 52 taper(s) at feature edges and 1 spot(s) too small to be a wall (0.22% of surface, budget 2%); 51 more within measurement error of the limit |
| thickness distribution | PASS | median 20.93 mm, p95 33.95 mm, max 34.44 mm |
| hollowable at 1.20 mm wall | WARN | 5.67 of 9.72 cm3 (58%) in 1 pocket(s) |
| filament that would save | PASS | 0.85 cm3, 1.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.14 mm | (5.3, 7.9, 7.1) | 50 | 1.3 | 4.5 | 0.30 |
| 2 | taper | 0.14 mm | (6.0, 8.1, 19.0) | 46 | 1.2 | 3.6 | 0.34 |
| 3 | spot | 0.21 mm | (2.4, -8.3, 19.9) | 33 | 1.1 | 1.1 | 1.03 |
| 4 | taper | 0.14 mm | (10.4, 2.1, 15.5) | 17 | 0.7 | 0.9 | 0.76 |
| 5 | taper | 0.21 mm | (-1.3, 3.8, 24.3) | 19 | 0.6 | 2.2 | 0.27 |
| 6 | taper | 0.21 mm | (-6.9, -6.3, 6.8) | 20 | 0.5 | 2.4 | 0.22 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
