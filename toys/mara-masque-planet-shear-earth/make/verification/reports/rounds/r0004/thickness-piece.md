# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_piece.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0004/thickness-piece.md`

part_piece.step.py: 9.74 cm3 solid, grid 0.140 mm (247x251x184), 178151 surface samples, thickness resolved to 0.070 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.3% of surface below (333 of 178151 samples); thinnest 0.14 mm at (-1.7, 4.3, 23.4) in 49 region(s); no region is a wall, 47 taper(s) at feature edges and 2 spot(s) too small to be a wall (0.27% of surface, budget 2%); 71 more within measurement error of the limit |
| thickness distribution | PASS | median 20.93 mm, p95 33.95 mm, max 34.51 mm |
| hollowable at 1.20 mm wall | WARN | 5.74 of 9.74 cm3 (59%) in 1 pocket(s) |
| filament that would save | PASS | 0.86 cm3, 1.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.14 mm | (3.0, 8.7, 6.6) | 60 | 1.9 | 6.2 | 0.30 |
| 2 | taper | 0.14 mm | (6.0, 8.1, 19.1) | 69 | 1.8 | 6.2 | 0.29 |
| 3 | spot | 0.14 mm | (2.3, -8.7, 20.3) | 27 | 1.1 | 1.1 | 0.92 |
| 4 | spot | 0.21 mm | (10.5, 2.1, 15.6) | 19 | 0.9 | 1.1 | 0.83 |
| 5 | taper | 0.14 mm | (11.0, -3.0, 15.3) | 9 | 0.4 | 1.0 | 0.43 |
| 6 | taper | 0.21 mm | (-0.1, -3.7, 23.8) | 14 | 0.4 | 0.6 | 0.64 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
