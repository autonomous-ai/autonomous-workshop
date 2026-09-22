# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_lane_20_cocoa_brown.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0003/thickness-lane_20_cocoa_brown.md`

part_lane_20_cocoa_brown.step.py: 2.20 cm3 solid, grid 0.133 mm (448x320x35), 121947 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (269 of 121947 samples); thinnest 0.13 mm at (-69.5, 52.6, 0.1) in 2 region(s); no region is a wall, 2 taper(s) at feature edges (0.00% of surface, budget 2%); 8 more within measurement error of the limit |
| thickness distribution | PASS | median 2.80 mm, p95 15.18 mm, max 63.67 mm |
| hollowable at 1.20 mm wall | WARN | 0.23 of 2.20 cm3 (10%) in 1 pocket(s) |
| filament that would save | PASS | 0.03 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.20 mm | (-80.3, 33.8, 0.1) | 126 | 0.0 | 0.8 | 0.06 |
| 2 | taper | 0.13 mm | (-69.5, 52.6, 0.1) | 143 | 0.0 | 0.7 | 0.05 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
