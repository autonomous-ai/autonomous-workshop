# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_lane_24_cocoa_brown.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/lane_24_cocoa_brown/r0001/thickness-lane_24_cocoa_brown.md`

part_lane_24_cocoa_brown.step.py: 2.15 cm3 solid, grid 0.133 mm (168x481x35), 121094 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (211 of 121094 samples); thinnest 0.13 mm at (10.8, 89.1, 0.1) in 3 region(s); no region is a wall, 3 taper(s) at feature edges (0.00% of surface, budget 2%); 10 more within measurement error of the limit |
| thickness distribution | PASS | median 2.80 mm, p95 14.80 mm, max 63.87 mm |
| hollowable at 1.20 mm wall | WARN | 0.22 of 2.15 cm3 (10%) in 1 pocket(s) |
| filament that would save | PASS | 0.03 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.40 mm | (-2.5, 26.4, 2.3) | 1 | 0.0 | 0.0 | 0.13 |
| 2 | taper | 0.13 mm | (10.8, 89.1, 0.1) | 103 | 0.0 | 0.7 | 0.02 |
| 3 | taper | 0.13 mm | (-10.9, 87.3, 0.1) | 107 | 0.0 | 0.7 | 0.01 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
