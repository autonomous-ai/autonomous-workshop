# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_piece.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/piece/r0003/thickness-piece.md`

part_piece.step.py: 9.80 cm3 solid, grid 0.140 mm (247x251x188), 182865 surface samples, thickness resolved to 0.070 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.3% of surface below (381 of 182865 samples); thinnest 0.14 mm at (-2.5, -16.7, 0.0) in 46 region(s); no region is a wall, 44 taper(s) at feature edges and 2 spot(s) too small to be a wall (0.27% of surface, budget 2%); 78 more within measurement error of the limit |
| thickness distribution | PASS | median 20.79 mm, p95 33.95 mm, max 34.44 mm |
| hollowable at 1.20 mm wall | WARN | 5.72 of 9.80 cm3 (58%) in 1 pocket(s) |
| filament that would save | PASS | 0.86 cm3, 1.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.14 mm | (2.4, 8.8, 7.1) | 75 | 1.8 | 6.1 | 0.30 |
| 2 | taper | 0.14 mm | (-4.3, -8.8, 8.0) | 58 | 1.5 | 6.6 | 0.23 |
| 3 | taper | 0.14 mm | (3.8, 7.7, 21.7) | 44 | 1.2 | 5.1 | 0.23 |
| 4 | taper | 0.14 mm | (4.6, -8.3, 20.6) | 43 | 1.1 | 5.9 | 0.18 |
| 5 | taper | 0.14 mm | (2.3, -8.7, 20.9) | 29 | 0.9 | 1.2 | 0.75 |
| 6 | spot | 0.21 mm | (10.6, 2.2, 16.2) | 19 | 0.8 | 1.0 | 0.85 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
