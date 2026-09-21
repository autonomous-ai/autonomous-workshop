# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_lane_11_yellow.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/thickness-lane_11_yellow.md`

part_lane_11_yellow.step.py: 2.21 cm3 solid, grid 0.133 mm (221x485x35), 122624 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (264 of 122624 samples); thinnest 0.13 mm at (32.9, -80.8, 0.1) in 2 region(s); no region is a wall, 2 taper(s) at feature edges (0.00% of surface, budget 2%); 6 more within measurement error of the limit |
| thickness distribution | PASS | median 2.80 mm, p95 14.46 mm, max 63.40 mm |
| hollowable at 1.20 mm wall | WARN | 0.23 of 2.21 cm3 (10%) in 1 pocket(s) |
| filament that would save | PASS | 0.03 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (32.9, -80.8, 0.1) | 143 | 0.1 | 0.7 | 0.07 |
| 2 | taper | 0.33 mm | (12.1, -87.7, 0.1) | 121 | 0.0 | 0.6 | 0.03 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
