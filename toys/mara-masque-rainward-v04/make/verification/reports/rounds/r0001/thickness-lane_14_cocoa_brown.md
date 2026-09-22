# Thickness and hollow

`<WORKSHOP_RUN>/artifacts/make/r0001/product/cad/part_lane_14_cocoa_brown.step.py --nozzle 0.4 --report <WORKSHOP_RUN>/artifacts/make/r0001/product/cad/measure/rounds/r0001/thickness-lane_14_cocoa_brown.md`

part_lane_14_cocoa_brown.step.py: 2.21 cm3 solid, grid 0.133 mm (320x451x35), 122857 surface samples, thickness resolved to 0.067 mm

| check | status | detail |
|---|---|---|
| wall >= 0.80 mm (+/-0.07) | PASS | 0.0% of surface below (314 of 122857 samples); thinnest 0.13 mm at (-52.6, -69.5, 0.1) in 3 region(s); no region is a wall, 3 taper(s) at feature edges (0.01% of surface, budget 2%); 18 more within measurement error of the limit |
| thickness distribution | PASS | median 2.80 mm, p95 15.07 mm, max 63.40 mm |
| hollowable at 1.20 mm wall | WARN | 0.23 of 2.21 cm3 (10%) in 1 pocket(s) |
| filament that would save | PASS | 0.03 cm3, 0.0 g at 15% infill -- the slicer already leaves most of that space empty |


## Thin regions, worst first

A `wall` is thin over its face and fails. A `taper` is the tip of a wedge where two faces meet -- its sub-minimum band is narrower than one minimum wall, so the slicer drops less than a wall's width of material at that edge. A `spot` is too short to run a nozzle along at all, and is usually the surface normal misbehaving at a sharp convex corner.

| # | kind | thinnest | at | samples | area mm2 | runs mm | band mm |
|---|---|---|---|---|---|---|---|
| 1 | taper | 0.13 mm | (-34.0, -80.7, 0.1) | 139 | 0.1 | 0.7 | 0.11 |
| 2 | taper | 0.13 mm | (-52.6, -69.5, 0.1) | 174 | 0.0 | 0.8 | 0.04 |
| 3 | taper | 0.13 mm | (-15.3, -21.6, 2.3) | 1 | 0.0 | 0.0 | 0.13 |

RESULT: printable at this wall

Measured on the entry's tessellated solid. The fix belongs in the
generator --
see `references/print-optimisation.md` and `scripts/cadprint.py`.
