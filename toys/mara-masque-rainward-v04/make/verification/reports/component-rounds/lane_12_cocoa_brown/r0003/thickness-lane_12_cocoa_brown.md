# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_lane_12_cocoa_brown.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/lane_12_cocoa_brown/r0003/thickness-lane_12_cocoa_brown.md`

part_lane_12_cocoa_brown.step.py: 2.14 cm3 solid, grid 0.133 mm (165x481x35), 119004 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (102 of 119004 samples); thinnest 0.13 mm at (10.9, -86.9, 0.1) in 2 region(s); no region is a wall, 2 taper(s) at feature edges (0.00% of surface, budget 2%); 7 more within measurement error of the limit |
| thickness distribution | PASS | median 2.80 mm, p95 14.93 mm, max 63.53 mm |
| hollowable at 1.20 mm wall | WARN | 0.22 of 2.14 cm3 (10%) in 1 pocket(s) |
| filament that would save | PASS | 0.03 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (10.9, -86.9, 0.1) | 56 | 0.0 | 0.7 | 0.06 |
| 2 | taper | 0.20 mm | (-10.5, -87.0, 0.1) | 46 | 0.0 | 0.8 | 0.05 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
