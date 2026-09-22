# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_lane_05_yellow.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/lane_05_yellow/r0001/thickness-lane_05_yellow.md`

part_lane_05_yellow.step.py: 2.22 cm3 solid, grid 0.133 mm (487x229x35), 117494 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (9 of 117494 samples); thinnest 0.27 mm at (24.7, 9.6, 0.1) in 5 region(s); no region is a wall, 5 taper(s) at feature edges (0.01% of surface, budget 2%); 4 more within measurement error of the limit |
| thickness distribution | PASS | median 2.80 mm, p95 13.33 mm, max 63.53 mm |
| hollowable at 1.20 mm wall | WARN | 0.23 of 2.22 cm3 (10%) in 1 pocket(s) |
| filament that would save | PASS | 0.03 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.40 mm | (85.0, 28.9, 1.0) | 3 | 0.1 | 0.6 | 0.08 |
| 2 | taper | 0.53 mm | (83.4, 12.2, 2.8) | 1 | 0.0 | 0.0 | 0.15 |
| 3 | taper | 0.67 mm | (88.2, 16.8, 0.9) | 1 | 0.0 | 0.0 | 0.13 |
| 4 | taper | 0.53 mm | (83.4, 33.3, 1.0) | 1 | 0.0 | 0.0 | 0.13 |
| 5 | taper | 0.27 mm | (24.7, 9.6, 0.1) | 3 | 0.0 | 0.1 | 0.01 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
