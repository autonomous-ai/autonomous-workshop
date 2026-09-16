# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_piece.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/piece/r0002/thickness-piece.md`

part_piece.step.py: 9.84 cm3 solid, grid 0.140 mm (247x250x190), 183636 surface samples, thickness resolved to 0.070 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.2% of surface below (327 of 183636 samples); thinnest 0.14 mm at (-5.8, -9.9, 15.5) in 49 region(s); no region is a wall, 47 taper(s) at feature edges and 2 spot(s) too small to be a wall (0.23% of surface, budget 2%); 103 more within measurement error of the limit |
| thickness distribution | PASS | median 20.93 mm, p95 33.95 mm, max 34.37 mm |
| hollowable at 1.20 mm wall | WARN | 5.78 of 9.84 cm3 (59%) in 1 pocket(s) |
| filament that would save | PASS | 0.87 cm3, 1.1 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.14 mm | (5.2, 8.1, 20.7) | 61 | 1.6 | 7.3 | 0.22 |
| 2 | taper | 0.14 mm | (5.3, 8.0, 7.9) | 44 | 1.1 | 5.6 | 0.20 |
| 3 | taper | 0.21 mm | (3.4, -9.6, 19.8) | 42 | 1.1 | 6.7 | 0.16 |
| 4 | spot | 0.21 mm | (10.5, 2.3, 16.5) | 26 | 1.0 | 0.9 | 1.05 |
| 5 | spot | 0.14 mm | (2.5, -8.7, 21.0) | 21 | 0.9 | 0.9 | 1.08 |
| 6 | taper | 0.35 mm | (-7.6, -7.4, 18.5) | 16 | 0.4 | 2.6 | 0.17 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
