# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_lane_16_cocoa_brown.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/lane_16_cocoa_brown/r0001/thickness-lane_16_cocoa_brown.md`

part_lane_16_cocoa_brown.step.py: 2.22 cm3 solid, grid 0.133 mm (465x332x35), 117477 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (10 of 117477 samples); thinnest 0.27 mm at (-80.7, -39.4, 1.0) in 6 region(s); no region is a wall, 6 taper(s) at feature edges (0.00% of surface, budget 2%); 1 more within measurement error of the limit |
| thickness distribution | PASS | median 2.80 mm, p95 13.27 mm, max 63.60 mm |
| hollowable at 1.20 mm wall | WARN | 0.23 of 2.22 cm3 (10%) in 1 pocket(s) |
| filament that would save | PASS | 0.03 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.27 mm | (-80.7, -39.4, 1.0) | 2 | 0.0 | 0.2 | 0.15 |
| 2 | taper | 0.33 mm | (-72.9, -52.4, 1.0) | 2 | 0.0 | 0.4 | 0.08 |
| 3 | taper | 0.67 mm | (-74.4, -50.2, 1.0) | 1 | 0.0 | 0.0 | 0.13 |
| 4 | taper | 0.60 mm | (-73.6, -51.4, 1.0) | 1 | 0.0 | 0.0 | 0.13 |
| 5 | taper | 0.47 mm | (-21.4, -15.7, 0.1) | 3 | 0.0 | 0.0 | 0.01 |
| 6 | taper | 0.73 mm | (-24.3, -10.7, 0.0) | 1 | 0.0 | 0.0 | 0.00 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
