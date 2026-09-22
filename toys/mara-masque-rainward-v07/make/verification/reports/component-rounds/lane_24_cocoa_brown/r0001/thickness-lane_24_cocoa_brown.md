# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_lane_24_cocoa_brown.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/component-rounds/lane_24_cocoa_brown/r0001/thickness-lane_24_cocoa_brown.md`

part_lane_24_cocoa_brown.step.py: 1.34 cm3 solid, grid 0.133 mm (153x403x27), 87061 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (7 of 87061 samples); thinnest 0.20 mm at (2.9, 26.3, 0.1) in 4 region(s); no region is a wall, 4 taper(s) at feature edges (0.00% of surface, budget 2%); 26 more within measurement error of the limit |
| thickness distribution | PASS | median 2.13 mm, p95 9.40 mm, max 53.13 mm |
| hollowable at 1.20 mm wall | PASS | 0.00 of 1.34 cm3 (0%) in 0 pocket(s) |
| filament that would save | PASS | 0.00 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.20 mm | (-3.5, 76.4, 2.2) | 2 | 0.0 | 0.3 | 0.11 |
| 2 | taper | 0.60 mm | (-6.5, 79.2, 0.9) | 1 | 0.0 | 0.0 | 0.14 |
| 3 | taper | 0.20 mm | (2.9, 26.3, 0.1) | 3 | 0.0 | 0.1 | 0.01 |
| 4 | taper | 0.60 mm | (-3.0, 26.3, 0.1) | 1 | 0.0 | 0.0 | 0.00 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
