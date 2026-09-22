# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_lane_22_cocoa_brown.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/thickness-lane_22_cocoa_brown.md`

part_lane_22_cocoa_brown.step.py: 1.35 cm3 solid, grid 0.133 mm (285x395x27), 87121 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (12 of 87121 samples); thinnest 0.20 mm at (-15.7, 21.3, 0.1) in 4 region(s); no region is a wall, 4 taper(s) at feature edges (0.00% of surface, budget 2%); 35 more within measurement error of the limit |
| thickness distribution | PASS | median 2.13 mm, p95 9.60 mm, max 53.20 mm |
| hollowable at 1.20 mm wall | PASS | 0.00 of 1.35 cm3 (0%) in 0 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.33 mm | (-44.4, 66.0, 1.0) | 1 | 0.0 | 0.0 | 0.14 |
| 2 | taper | 0.27 mm | (-10.6, 24.3, 0.1) | 7 | 0.0 | 0.1 | 0.02 |
| 3 | taper | 0.20 mm | (-15.7, 21.3, 0.1) | 3 | 0.0 | 0.0 | 0.01 |
| 4 | taper | 0.67 mm | (-31.0, 73.1, 0.0) | 1 | 0.0 | 0.0 | 0.00 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
