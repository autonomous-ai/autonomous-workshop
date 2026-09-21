# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_lane_23_yellow.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/thickness-lane_23_yellow.md`

part_lane_23_yellow.step.py: 1.35 cm3 solid, grid 0.133 mm (200x411x27), 87058 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (13 of 87058 samples); thinnest 0.20 mm at (-9.7, 24.7, 0.1) in 5 region(s); no region is a wall, 5 taper(s) at feature edges (0.01% of surface, budget 2%); 33 more within measurement error of the limit |
| thickness distribution | PASS | median 2.13 mm, p95 9.33 mm, max 53.20 mm |
| hollowable at 1.20 mm wall | PASS | 0.00 of 1.35 cm3 (0%) in 0 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.20 mm | (-23.1, 72.8, 2.2) | 2 | 0.0 | 0.3 | 0.11 |
| 2 | taper | 0.67 mm | (-16.3, 77.8, 0.1) | 2 | 0.0 | 0.1 | 0.23 |
| 3 | taper | 0.60 mm | (-26.8, 74.8, 0.9) | 1 | 0.0 | 0.0 | 0.14 |
| 4 | taper | 0.20 mm | (-9.7, 24.7, 0.1) | 5 | 0.0 | 0.2 | 0.01 |
| 5 | taper | 0.33 mm | (-4.0, 26.2, 0.1) | 3 | 0.0 | 0.1 | 0.01 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
