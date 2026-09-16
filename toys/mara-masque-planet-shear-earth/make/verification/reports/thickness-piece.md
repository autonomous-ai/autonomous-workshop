# Thickness and hollow

`artifacts/make/r0001/product/cad/part_piece.step.py --nozzle 0.4 --report artifacts/make/r0001/product/cad/measure/thickness-piece.md`

part_piece.step.py: 9.75 cm3 solid, grid 0.140 mm (247x251x184), 178010 surface samples, thickness resolved to 0.070 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.2% of surface below (283 of 178010 samples); thinnest 0.14 mm at (10.9, 2.3, 15.9) in 48 region(s); no region is a wall, 47 taper(s) at feature edges and 1 spot(s) too small to be a wall (0.23% of surface, budget 2%); 56 more within measurement error of the limit |
| thickness distribution | PASS | median 20.93 mm, p95 33.95 mm, max 34.44 mm |
| hollowable at 1.20 mm wall | WARN | 5.75 of 9.75 cm3 (59%) in 1 pocket(s) |
| filament that would save | PASS | 0.86 cm3, 1.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.14 mm | (4.3, 8.7, 7.2) | 60 | 1.9 | 5.8 | 0.33 |
| 2 | spot | 0.14 mm | (2.3, -8.7, 20.3) | 29 | 1.1 | 1.2 | 0.95 |
| 3 | taper | 0.14 mm | (6.6, 7.9, 18.6) | 35 | 0.8 | 4.9 | 0.16 |
| 4 | taper | 0.14 mm | (10.9, 2.3, 15.9) | 15 | 0.6 | 1.2 | 0.49 |
| 5 | taper | 0.14 mm | (2.3, 7.3, 22.2) | 16 | 0.5 | 1.5 | 0.32 |
| 6 | taper | 0.14 mm | (-1.7, 4.3, 23.4) | 14 | 0.4 | 2.1 | 0.21 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
