# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_lane_11_yellow.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/thickness-lane_11_yellow.md`

part_lane_11_yellow.step.py: 2.22 cm3 solid, grid 0.133 mm (229x487x35), 117448 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (8 of 117448 samples); thinnest 0.13 mm at (9.6, -24.7, 0.1) in 5 region(s); no region is a wall, 5 taper(s) at feature edges (0.00% of surface, budget 2%); 1 more within measurement error of the limit |
| thickness distribution | PASS | median 2.80 mm, p95 13.31 mm, max 63.60 mm |
| hollowable at 1.20 mm wall | WARN | 0.23 of 2.22 cm3 (10%) in 1 pocket(s) |
| filament that would save | PASS | 0.03 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.27 mm | (29.5, -84.8, 1.0) | 2 | 0.0 | 0.7 | 0.05 |
| 2 | taper | 0.73 mm | (18.2, -87.9, 0.1) | 1 | 0.0 | 0.0 | 0.13 |
| 3 | taper | 0.27 mm | (17.2, -88.1, 1.0) | 1 | 0.0 | 0.0 | 0.13 |
| 4 | taper | 0.27 mm | (33.1, -83.5, 1.0) | 1 | 0.0 | 0.0 | 0.13 |
| 5 | taper | 0.13 mm | (9.6, -24.7, 0.1) | 3 | 0.0 | 0.0 | 0.01 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
