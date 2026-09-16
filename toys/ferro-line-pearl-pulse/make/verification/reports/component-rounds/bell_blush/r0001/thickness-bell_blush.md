# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_bell_blush.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/bell_blush/r0001/thickness-bell_blush.md`

part_bell_blush.step.py: 0.30 cm3 solid, grid 0.133 mm (112x193x140), 32916 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | FAIL | 11.1% of surface below (3660 of 32916 samples); thinnest 0.20 mm at (16.5, 35.5, 17.7) in 8 region(s); 2 wall(s) (widest band 7.23 mm), 6 taper(s) at feature edges (0.06% of surface, budget 2%); 26 more within measurement error of the limit |
| thickness distribution | PASS | median 1.13 mm, p95 6.27 mm, max 12.80 mm |
| hollowable at 1.20 mm wall | PASS | 0.00 of 0.30 cm3 (0%) in 0 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | wall | 0.27 mm | (4.6, 20.9, 1.4) | 3119 | 60.0 | 8.3 | 7.23 |
| 2 | wall | 0.20 mm | (13.6, 38.3, 17.8) | 522 | 10.2 | 9.8 | 1.04 |
| 3 | taper | 0.27 mm | (11.5, 24.7, 0.3) | 13 | 0.3 | 1.0 | 0.26 |
| 4 | taper | 0.40 mm | (6.4, 32.8, 9.1) | 2 | 0.0 | 0.3 | 0.11 |
| 5 | taper | 0.67 mm | (12.2, 26.3, 2.8) | 1 | 0.0 | 0.0 | 0.17 |
| 6 | taper | 0.60 mm | (16.2, 34.7, 16.4) | 1 | 0.0 | 0.0 | 0.17 |

RESULT: WALL BELOW MINIMUM

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
