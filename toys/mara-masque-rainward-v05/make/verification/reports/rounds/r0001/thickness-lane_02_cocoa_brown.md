# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_lane_02_cocoa_brown.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/thickness-lane_02_cocoa_brown.md`

part_lane_02_cocoa_brown.step.py: 2.22 cm3 solid, grid 0.133 mm (332x466x35), 117465 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (7 of 117465 samples); thinnest 0.33 mm at (50.1, 74.5, 1.0) in 5 region(s); no region is a wall, 5 taper(s) at feature edges (0.00% of surface, budget 2%); 1 more within measurement error of the limit |
| thickness distribution | PASS | median 2.80 mm, p95 13.33 mm, max 63.53 mm |
| hollowable at 1.20 mm wall | WARN | 0.23 of 2.22 cm3 (10%) in 1 pocket(s) |
| filament that would save | PASS | 0.03 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.33 mm | (50.1, 74.5, 1.0) | 2 | 0.0 | 0.3 | 0.11 |
| 2 | taper | 0.53 mm | (38.3, 81.2, 1.0) | 2 | 0.0 | 0.8 | 0.04 |
| 3 | taper | 0.47 mm | (35.7, 82.4, 1.0) | 1 | 0.0 | 0.0 | 0.13 |
| 4 | taper | 0.73 mm | (10.7, 24.3, 0.1) | 1 | 0.0 | 0.0 | 0.00 |
| 5 | taper | 0.33 mm | (15.7, 21.5, 0.0) | 1 | 0.0 | 0.0 | 0.00 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
